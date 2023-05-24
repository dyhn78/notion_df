import json
from pathlib import Path
from typing import Optional, cast

from notion_df.entity import Entity, Page
from notion_df.object.property import RelationProperty, PageProperties
from notion_df.request.request_core import Response_T
from notion_df.util.collection import Paginator
from notion_df.util.misc import get_generic_arg
from workflow import workflow_path
from workflow.action.action_core import IterableAction
from workflow.constant.block_enum import DatabaseEnum


class ResponseBackupService:
    def __init__(self, root: Path):
        self.root = root

    def _get_path(self, entity: Entity) -> Path:
        return self.root / f'{entity.id}.json'

    def read(self, entity: Entity[Response_T]) -> Optional[Response_T]:
        path = self._get_path(entity)
        if not path.is_file():
            return
        with path.open('r') as file:
            response_raw_data = json.load(file)
        return get_generic_arg(type(entity), Response_T).deserialize(response_raw_data)

    def write(self, entity: Entity[Response_T]):
        path = self._get_path(entity)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            print(f'\t{entity} -> overwrite ({self.read(entity).timestamp})')
        else:
            print(f'\t{entity} -> create')
        with path.open('w') as file:
            json.dump(entity.last_response.raw_data, file, indent=2)


class MigrationBackupSaveAction(IterableAction):
    def __init__(self, backup_path: Path):
        self.backup = ResponseBackupService(backup_path)

    def query_all(self) -> Paginator[Page]:
        return DatabaseEnum.event_db.entity.query(page_size=1)
        # results = []
        # for db_enum in DatabaseEnum:
        #     results.append(db_enum.entity.query())
        # return Paginator.chain(Page, results)

    def filter(self, page: Page) -> bool:
        return True

    def process_page(self, page: Page):
        self.backup.write(page)


class MigrationBackupLoadAction(IterableAction):
    def __init__(self, backup_path: Path):
        self.response_backup = ResponseBackupService(backup_path)

    def query_all(self) -> Paginator[Page]:
        return Paginator.empty(Page)

    def filter(self, page: Page) -> bool:
        return DatabaseEnum.from_entity(page.parent) is not None

    def process_page(self, this_page: Page):
        this_prev_response = self.response_backup.read(this_page)
        this_prev_parent = this_prev_response.parent.entity
        if this_prev_parent == this_page.parent:
            return
        this_db_enum: DatabaseEnum = DatabaseEnum.from_entity(this_page.parent)
        this_prev_db_enum: Optional[DatabaseEnum] = DatabaseEnum.from_entity(this_prev_parent)

        this_new_properties = PageProperties()
        for this_prev_prop, this_prev_prop_value in this_prev_response.properties.items():
            if not isinstance(this_prev_prop, RelationProperty):
                continue
            for linked_page in cast(this_prev_prop.page_value, this_prev_prop_value):
                try:
                    linked_db = linked_page.parent
                except AttributeError:
                    linked_db = self.response_backup.read(linked_page).parent.entity
                if not (linked_db_enum := DatabaseEnum.from_entity(linked_db)):
                    continue
                new_prop: RelationProperty = self.find_new_relation_property(this_db_enum, this_prev_db_enum,
                                                                             linked_db_enum, this_prev_prop)
                this_new_properties.setdefault(new_prop, new_prop.page_value()).append(linked_page)
        this_page.update(this_new_properties)

    @classmethod
    def find_new_relation_property(
            cls, this_db_enum: DatabaseEnum, this_prev_db_enum: Optional[DatabaseEnum],
            linked_db_enum: DatabaseEnum, this_prev_prop: RelationProperty) -> Optional[RelationProperty]:
        for db_enum in this_db_enum, linked_db_enum:
            if not db_enum.entity.last_response:
                db_enum.entity.retrieve()

        if this_prev_prop in this_db_enum.entity.properties:
            return this_prev_prop

        # TODO: add a custom mapping from (linked_db_enum, this_db_enum, this_prop)
        #  to (linked_db_enum, this_new_db_enum, **this_new_prop**)

        # default scenario
        candidate_props: list[RelationProperty] = []
        for prop in this_db_enum.entity.properties:
            if not isinstance(prop, RelationProperty):
                continue
            if this_db_enum.entity.properties[prop].database == linked_db_enum.entity:
                candidate_props.append(prop)
        if not candidate_props:
            return
        for prop in candidate_props:
            if prop.name == linked_db_enum.prefix_title:
                return prop
        return candidate_props[0]


if __name__ == '__main__':
    MigrationBackupSaveAction(workflow_path.parent / 'backup').execute_all()
