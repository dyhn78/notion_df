from typing import Optional

from notion_df.entity import Namespace, Page
from notion_df.object.block import ChildPageBlockValue
from notion_df.object.common import SelectOption
from notion_df.object.filter import CompoundFilter
from notion_df.property import SelectPropertyKey, CheckboxFormulaPropertyKey, TitlePropertyKey, RichTextPropertyKey, \
    URLPropertyKey, NumberPropertyKey, FilesPropertyKey, CheckboxPropertyKey, PageProperties
from notion_df.util.collection import StrEnum
from workflow.constant.block_enum import DatabaseEnum
from workflow.service.lib_gy_service import GoyangLibraryScraper
from workflow.service.webdriver_service import WebDriverFactory
from workflow.service.yes24_service import get_yes24_detail_page_url, Yes24ScrapResult, get_block_value_of_contents_line
from workflow.util.action import Action

edit_status_key = SelectPropertyKey('🔰준비')
media_type_key = SelectPropertyKey('📘유형')
is_book_key = CheckboxFormulaPropertyKey('📔도서류')
title_key = TitlePropertyKey('📚제목')
true_name_key = RichTextPropertyKey('📚원제(검색용)')
sub_name_key = RichTextPropertyKey('📚부제')
url_key = URLPropertyKey('📚링크')
author_key = RichTextPropertyKey('📚만든이')
publisher_key = RichTextPropertyKey('📚만든곳')
volume_key = NumberPropertyKey('📚N(쪽)')
cover_image_key = FilesPropertyKey('📚표지')
location_key = RichTextPropertyKey('📚위치')
not_available_key = CheckboxPropertyKey('📚대출중')
link_to_contents_key = RichTextPropertyKey('📦결속')


class EditStatusValue(StrEnum):
    default = '📥본문/위치(비파괴)'
    metadata_overwrite = '📥본문(파괴)'
    location_overwrite = '📥위치(파괴)'
    complete = '⛳수합 완료'
    fill_manually = '👤직접 입력'
    confirm_manually = '👤결과 검정'


class ReadingMediaScraper(Action):
    def __init__(self, namespace: Namespace):
        self.namespace = namespace
        self.readings = self.namespace.database(DatabaseEnum.readings.id)
        self.factory = WebDriverFactory(create_window=True)
        self.gy_scraper = GoyangLibraryScraper(self.factory())

    def execute(self):
        reading_list = self.readings.query(is_book_key.filter.equals(True) & CompoundFilter('or', [
            edit_status_key.filter.equals(option) for option in
            [EditStatusValue.default, EditStatusValue.metadata_overwrite, EditStatusValue.location_overwrite, None]
        ]))
        for reading in reading_list:
            ReadingMediaScraperUnit(self, reading).execute()


class ReadingMediaScraperUnit:
    def __init__(self, action: ReadingMediaScraper, reading: Page):
        self.action = action
        self.namespace = action.namespace
        self.gy_scraper = action.gy_scraper

        self.reading = reading
        self.new_properties = PageProperties()
        self.title = self.reading.properties[title_key].plain_text
        self.true_name = self.reading.properties[true_name_key].plain_text

    def execute(self) -> None:
        new_status_value = EditStatusValue.fill_manually
        match self.reading.properties[edit_status_key].name:
            case EditStatusValue.default:
                if self.process_yes24(False) and self.process_lib_gy(False):
                    new_status_value = EditStatusValue.confirm_manually
            case EditStatusValue.metadata_overwrite:
                if self.process_yes24(True):
                    new_status_value = EditStatusValue.complete
            case EditStatusValue.location_overwrite:
                if self.process_lib_gy(True):
                    new_status_value = EditStatusValue.complete
        self.new_properties[edit_status_key] = SelectOption(new_status_value)
        self.reading.update(self.new_properties)

    def process_yes24(self, overwrite: bool) -> bool:
        if url := self.reading.properties[url_key]:
            pass
        elif url := get_yes24_detail_page_url(self.title):
            pass
        elif url := get_yes24_detail_page_url(self.true_name):
            pass
        else:
            return False
        result = Yes24ScrapResult.scrap(url)
        if overwrite:
            for key in true_name_key, sub_name_key, author_key, publisher_key, volume_key, cover_image_key:
                self.reading.properties.pop(key, None)
        if not self.reading.properties.get(true_name_key):
            self.new_properties[true_name_key] = true_name_key.page.from_plain_text(result.get_true_name())
        if not self.reading.properties.get(sub_name_key):
            self.new_properties[sub_name_key] = sub_name_key.page.from_plain_text(result.get_sub_name())
        if not self.reading.properties.get(author_key):
            self.new_properties[author_key] = author_key.page.from_plain_text(result.get_author())
        if not self.reading.properties.get(publisher_key):
            self.new_properties[publisher_key] = publisher_key.page.from_plain_text(result.get_publisher())
        if not self.reading.properties.get(volume_key):
            self.new_properties[volume_key] = result.get_page_count()
        if not self.reading.properties.get(cover_image_key):
            self.new_properties[cover_image_key] = cover_image_key.page.externals([
                (result.get_cover_image_url(), self.title)])

        child_values = [get_block_value_of_contents_line(content_line) for content_line in result.get_contents()]
        content_page = self.get_content_page()
        if content_page and overwrite:
            content_page.update(archived=True)
            content_page = None
        if not content_page:
            content_page = self.create_content_page()
        content_page.as_block().append_children(child_values)
        return True

    def get_content_page(self) -> Optional[Page]:
        for block in self.reading.as_block().retrieve_children():
            if isinstance(block.value, ChildPageBlockValue):
                block_title = block.value.title
                if self.title in block_title or block_title.strip() in ['', '=', '>']:
                    return Page(self.namespace, block.id)

    def create_content_page(self) -> Page:
        title = self.reading.properties[title_key].plain_text
        return self.reading.create_child_page(PageProperties({
            TitlePropertyKey('title'): TitlePropertyKey.page.from_plain_text(f'>{title}')}))

    def process_lib_gy(self, overwrite: bool) -> bool:
        result = self.gy_scraper.process_page(self.true_name)
        if not result:
            return False
        if overwrite:
            self.reading.properties.pop(location_key, None)
            self.reading.properties.pop(not_available_key, None)
        if not self.reading.properties.get(location_key):
            self.new_properties[location_key] = location_key.page.from_plain_text(str(result))
            self.new_properties[not_available_key] = not result.availability
        return True
