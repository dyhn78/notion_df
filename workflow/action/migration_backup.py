import json
from pathlib import Path
from typing import Optional, cast, Iterator

from notion_df.entity import Entity, Page, Database
from notion_df.object.property import RelationProperty, PageProperties
from notion_df.request.request_core import Response_T
from notion_df.util.misc import get_generic_arg
from workflow import project_root
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
            print(f'\t{entity}\n\t\t-> overwrite ({self.read(entity).timestamp})')
        else:
            print(f'\t{entity}\n\t\t-> create')
        with path.open('w') as file:
            json.dump(entity.last_response.raw_data, file, indent=2)


class MigrationBackupSaveAction(IterableAction):
    def __init__(self, backup_path: Path):
        self.backup = ResponseBackupService(backup_path)

    def query_all(self) -> Iterator[Page]:
        # return DatabaseEnum.event_db.entity.query(page_size=1)
        for db_enum in DatabaseEnum:
            yield from db_enum.entity.query()

    def filter(self, page: Page) -> bool:
        return isinstance(page.parent, Database)

    def process_page(self, page: Page):
        self.backup.write(page)


class MigrationBackupLoadAction(IterableAction):
    def __init__(self, backup_path: Path):
        self.response_backup = ResponseBackupService(backup_path)

    def query_all(self) -> Iterator[Page]:
        return iter([])

    def filter(self, page: Page) -> bool:
        return DatabaseEnum.from_entity(page.parent) is not None

    def process_page(self, this_page: Page):
        this_db = this_page.parent
        this_prev_response = self.response_backup.read(this_page)
        if not this_prev_response:
            print(f'\t{this_page}: Skipped since no previous response backup')
            return
        this_prev_parent = this_prev_response.parent.entity
        if this_prev_parent == this_db:
            print(f'\t{this_page}: Did not change the parent database')
            return

        this_new_properties = PageProperties()
        for this_prev_prop, this_prev_prop_value in this_prev_response.properties.items():
            if not isinstance(this_prev_prop, RelationProperty):
                continue
            for linked_page in cast(this_prev_prop.page_value, this_prev_prop_value):
                if not linked_page.last_response:
                    linked_page.retrieve()
                linked_db = linked_page.parent
                linked_prev_response = self.response_backup.read(linked_page)
                if linked_prev_response:
                    linked_prev_db = linked_prev_response.parent.entity
                else:
                    linked_prev_db = linked_db
                new_prop: RelationProperty = self.find_new_relation_property(this_db, this_prev_parent, linked_db,
                                                                             linked_prev_db, this_prev_prop)
                this_new_properties.setdefault(new_prop, new_prop.page_value()).append(linked_page)
        this_page.update(this_new_properties)

    @classmethod
    def find_new_relation_property(
            cls, this_db: Database, this_prev_db: Optional[Database],
            linked_db: Database, linked_prev_db: Optional[Database],
            this_prev_prop: RelationProperty) -> Optional[RelationProperty]:
        """this method guarantee that the returning property is picked from its candidates (this_db.properties)"""
        this_db_enum = DatabaseEnum.from_entity(this_db)
        this_prev_db_enum = DatabaseEnum.from_entity(this_prev_db)
        linked_db_enum = DatabaseEnum.from_entity(linked_db)
        candidate_props: list[RelationProperty] = []

        if not this_db.last_response:
            this_db.retrieve()
        for prop in this_db.properties:
            if not isinstance(prop, RelationProperty):
                continue
            if this_db.properties[prop].database == linked_db:
                candidate_props.append(prop)
        if not candidate_props:
            return

        def pick(prop_name: str) -> Optional[RelationProperty]:
            for _prop in candidate_props:
                if _prop.name == prop_name:
                    return _prop

        # customized cases
        if linked_db_enum == DatabaseEnum.date_db:
            if this_prev_prop.name == '🟢생성':
                return pick(this_prev_prop.name)
            if this_prev_prop.name in ['🟢일간', '🟢시작']:
                return pick(this_prev_prop.name) or pick('🟢생성')
        if linked_db_enum == DatabaseEnum.week_db:
            if this_prev_prop.name == '💚생성':
                return pick(this_prev_prop.name)
            if this_prev_prop.name in ['💚주간', '💚시작']:
                return pick(this_prev_prop.name) or pick('💚생성')
        if this_db_enum == DatabaseEnum.event_db and linked_db_enum == DatabaseEnum.reading_db:
            return pick('🟡관계')
        if this_db_enum == DatabaseEnum.reading_db and linked_db_enum == DatabaseEnum.event_db:
            return pick('🔵관계')
        if this_db_enum == DatabaseEnum.issue_db and linked_db_enum == DatabaseEnum.stream_db:
            if this_prev_db_enum in [DatabaseEnum.topic_db, DatabaseEnum.subject_db]:
                return pick('🔴요소')
            else:
                return pick('🔴구성')

        # default cases
        if linked_db_enum:
            if prop := pick(linked_db_enum.prefix_title):
                return prop
        return candidate_props[0]


if __name__ == '__main__':
    query = MigrationBackupSaveAction(project_root / 'backup').execute_all()
    input()
