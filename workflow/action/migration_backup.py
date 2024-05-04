from functools import cache
from pathlib import Path
from typing import Optional, cast, Iterator, Iterable

import tenacity
from loguru import logger

from notion_df.core.request import RequestError
from notion_df.entity import Page, Database
from notion_df.object.data import PageContents
from notion_df.property import RelationProperty, PageProperties
from workflow.action.match import get_earliest_date
from workflow.block_enum import DatabaseEnum, SCHEDULE, START
from workflow.core.action import SequentialAction
from workflow.service.backup_service import ResponseBackupService


class MigrationBackupSaveAction(SequentialAction):
    def __init__(self, backup_dir: Path):
        self.backup = ResponseBackupService(backup_dir)

    def query(self) -> Iterable[Page]:
        return []

    def process_page(self, page: Page) -> None:
        if not isinstance(page.current.parent, Database):
            return
        for prop in page.current.properties:
            if not isinstance(prop, RelationProperty):
                continue
            prop_value = page.current.properties[prop]
            # TODO: resolve Notion 504 error
            #  https://notiondevs.slack.com/archives/C01CZTMG85C/p1701409539104549
            if prop_value.has_more:
                try:
                    page.retrieve_property_item(prop.id)
                except tenacity.RetryError:
                    logger.error(f'failed Page.retrieve_property_item({page}, prop={prop.name})')
                    pass               
        self.backup.write(page)


class MigrationBackupLoadAction(SequentialAction):
    def __init__(self, backup_dir: Path):
        self.response_backup = ResponseBackupService(backup_dir)

    def query(self) -> Iterable[Page]:
        return []

    def process_page(self, page: Page) -> None:
        # this_page: the global page, directly under one of the global dbs
        this_page = next((breadcrumb_page for breadcrumb_page in iter_breadcrumb(page)
                          if DatabaseEnum.from_entity(breadcrumb_page.current.parent) is not None), None)
        if this_page is None:
            logger.info(f'\t{page}: Moved outside DatabaseEnum')

        this_db: Database = this_page.current.parent
        this_prev_data: Optional[PageContents] = self.response_backup.read(page)
        if not this_prev_data:
            logger.info(f'\t{page}: No previous response backup')
            return
        this_prev_db = this_prev_data.parent
        if page == this_page and this_prev_db == this_db:
            logger.info(f'\t{page}: Did not change the parent database')
            return

        this_new_properties = PageProperties()
        for this_prev_prop, this_prev_prop_value in this_prev_data.properties.items():
            if not isinstance(this_prev_prop, RelationProperty):
                continue
            for linked_page in cast(Iterable[Page], this_prev_prop_value):

                linked_prev_data: PageContents = self.response_backup.read(linked_page)
                if linked_page.current:
                    linked_db = linked_page.current.parent
                    if linked_prev_data:
                        linked_prev_db = linked_prev_data.parent
                    else:
                        linked_prev_db = None
                elif linked_prev_data:
                    linked_db = linked_prev_db = linked_prev_data.parent
                else:
                    linked_db = linked_prev_db = linked_page.retrieve().current.parent
                candidate_props = self.get_candidate_props(this_db, linked_db)
                if not candidate_props:
                    continue
                if any(linked_page in this_page.current.properties[prop] for prop in candidate_props):
                    continue
                new_prop: RelationProperty = self.find_new_relation_property(this_db, this_prev_db, linked_db,
                                                                             linked_prev_db, this_prev_prop)
                if not new_prop:
                    continue
                this_new_properties.setdefault(new_prop, this_page.current.properties[new_prop])
                this_new_properties[new_prop].append(linked_page)
        for this_new_prop in this_new_properties:
            if any(stem in this_new_prop.name for stem in [START, ]):
                dates = cast(RelationProperty.page_value, this_new_properties[this_new_prop])
                this_new_properties[this_new_prop] = RelationProperty.page_value([get_earliest_date(dates)])
        if not this_new_properties:
            return
        try:
            this_page.update(this_new_properties)
            return
        except RequestError as e:
            if (e.code == 'object_not_found') or ('Unsaved transactions' in e.message):
                for prop in this_new_properties:
                    this_new_properties[prop] = RelationProperty.page_value(
                        page for page in this_new_properties[prop] if page_exists(page))
                this_page.update(this_new_properties)
                return
            raise e
        finally:
            logger.info(f'\t{this_page}: {this_new_properties}')

    @classmethod
    @cache
    def get_candidate_props(cls, this_db: Database, linked_db: Database) -> list[RelationProperty]:
        candidate_props: list[RelationProperty] = []
        for prop in this_db.get().properties:
            if not isinstance(prop, RelationProperty):
                continue
            if this_db.current.properties[prop].database == linked_db:
                candidate_props.append(prop)
        return candidate_props

    @classmethod
    def find_new_relation_property(
            cls, this_db: Database, this_prev_db: Optional[Database],
            linked_db: Database, linked_prev_db: Optional[Database],
            this_prev_prop: RelationProperty) -> Optional[RelationProperty]:
        """this method guarantee that the returning property is picked from its candidates (this_db.properties)"""
        # TODO: if candidate_props is empty, create a mention-backlink instead
        # TODO: error handling on unique relational limit (provide related pages list on error message, etc.)
        this_db_enum = DatabaseEnum.from_entity(this_db)
        this_prev_db_enum = DatabaseEnum.from_entity(this_prev_db)
        linked_db_enum = DatabaseEnum.from_entity(linked_db)
        linked_prev_db_enum = DatabaseEnum.from_entity(linked_prev_db)
        candidate_props = cls.get_candidate_props(this_db, linked_db)

        def pick(_prop_name: str) -> Optional[RelationProperty]:
            return next((_prop for _prop in candidate_props if _prop_name in _prop.name), None)

        # customized cases
        if linked_db_enum == DatabaseEnum.datei_db:
            prefix = DatabaseEnum.datei_db.prefix
            prefix_title = DatabaseEnum.datei_db.prefix_title
            if this_prev_prop.name in [prefix_title, f'{prefix}{SCHEDULE}', f'{prefix}{START}']:
                return pick(this_prev_prop.name) or pick(prefix_title)
        if linked_db_enum == DatabaseEnum.weeki_db:
            prefix = DatabaseEnum.weeki_db.prefix
            prefix_title = DatabaseEnum.datei_db.prefix_title
            if this_prev_prop.name in [prefix_title, f'{prefix}{SCHEDULE}', f'{prefix}{START}']:
                return pick(this_prev_prop.name) or pick(prefix_title)
        if this_db_enum == linked_db_enum and this_prev_db_enum == linked_prev_db_enum:
            for prop_name_stem in ['구성', '공통', '요소', '관계']:
                if (prop_name_stem in this_prev_prop.name) and (prop_name := pick(prop_name_stem)):
                    return prop_name
        if this_db_enum == DatabaseEnum.event_db and linked_db_enum == DatabaseEnum.reading_db:
            return pick('관계')
        if this_db_enum == DatabaseEnum.reading_db and linked_db_enum == DatabaseEnum.event_db:
            return pick('관계')
        if this_db_enum == DatabaseEnum.issue_db and linked_db_enum == DatabaseEnum.issue_db:
            if this_prev_db_enum == DatabaseEnum.summit_db:
                return pick('요소')
        if this_db_enum == DatabaseEnum.summit_db and linked_db_enum == DatabaseEnum.summit_db:
            return pick('관계')

        # default cases
        if linked_db_enum:
            if prop := pick(linked_db_enum.prefix_title):
                return prop
        return candidate_props[0]


# TODO: integrate to base package
def iter_breadcrumb(page: Page) -> Iterator[Page]:
    page.get()
    yield page
    if page.current.parent is not None:
        yield from iter_breadcrumb(page.current.parent)


# TODO: integrate to base package
def page_exists(page: Page) -> bool:
    try:
        page.get()
        return True
    except RequestError:
        return False
