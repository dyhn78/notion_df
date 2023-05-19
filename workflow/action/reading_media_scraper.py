from typing import Optional

from notion_df.entity import Namespace, Page
from notion_df.object.block import ChildPageBlockValue
from notion_df.object.common import SelectOption
from notion_df.object.filter import CompoundFilter
from notion_df.property import SelectProperty, CheckboxFormulaProperty, TitleProperty, RichTextProperty, \
    URLProperty, NumberProperty, FilesProperty, CheckboxProperty, PageProperties
from notion_df.util.collection import StrEnum
from workflow.constant.block_enum import DatabaseEnum
from workflow.service.lib_gy_service import GYLibraryScraper
from workflow.service.webdriver_service import WebDriverFactory
from workflow.service.yes24_service import get_yes24_detail_page_url, Yes24ScrapResult, get_block_value_of_contents_line
from workflow.util.action import Action

edit_status = SelectProperty('🔰준비')
media_type = SelectProperty('📘유형')
is_book = CheckboxFormulaProperty('📔도서류')
title = TitleProperty('📚제목')
true_name = RichTextProperty('📚원제(검색용)')
sub_name = RichTextProperty('📚부제')
url = URLProperty('📚링크')
author = RichTextProperty('📚만든이')
publisher = RichTextProperty('📚만든곳')
volume = NumberProperty('📚N(쪽)')
cover_image = FilesProperty('📚표지')
location = RichTextProperty('📚위치')
not_available = CheckboxProperty('📚대출중')
link_to_contents = RichTextProperty('📦결속')


class EditStatusValue(StrEnum):
    default = '📥본문/위치(비파괴)'
    metadata_overwrite = '📥본문(파괴)'
    location_overwrite = '📥위치(파괴)'
    complete = '⛳수합 완료'
    fill_manually = '👤직접 입력'
    confirm_manually = '👤결과 검정'


class ReadingMediaScraper(Action):
    def __init__(self, namespace: Namespace, create_window: bool):
        self.namespace = namespace
        self.readings = self.namespace.database(DatabaseEnum.readings.id)
        self.factory = WebDriverFactory(create_window=create_window)
        self.gy_scraper = GYLibraryScraper(self.factory())

    def execute(self):
        reading_list = self.readings.query(is_book.filter.equals(True) & CompoundFilter('or', [
            edit_status.filter.equals(option) for option in
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
        self.title = self.reading.properties[title].plain_text
        self.true_name = self.reading.properties[true_name].plain_text

    def execute(self) -> None:
        new_status_value = EditStatusValue.fill_manually
        match getattr(self.reading.properties[edit_status], 'name', EditStatusValue.default):
            case EditStatusValue.default:
                if self.process_lib_gy(False) and self.process_yes24(False):
                    new_status_value = EditStatusValue.confirm_manually
            case EditStatusValue.metadata_overwrite:
                if self.process_yes24(True):
                    new_status_value = EditStatusValue.complete
            case EditStatusValue.location_overwrite:
                if self.process_lib_gy(True):
                    new_status_value = EditStatusValue.complete
        self.new_properties[edit_status] = SelectOption(new_status_value)
        self.reading.update(self.new_properties)

    def process_yes24(self, overwrite: bool) -> bool:
        if url_value := self.reading.properties[url]:
            pass
        elif url_value := get_yes24_detail_page_url(self.title):
            pass
        elif url_value := get_yes24_detail_page_url(self.true_name):
            pass
        else:
            return False
        result = Yes24ScrapResult.scrap(url_value)
        if overwrite:
            for key in true_name, sub_name, author, publisher, volume, cover_image:
                self.reading.properties.pop(key, None)
        if not self.reading.properties.get(true_name):
            self.new_properties[true_name] = true_name.page_value.from_plain_text(result.get_true_name())
        if not self.reading.properties.get(sub_name):
            self.new_properties[sub_name] = sub_name.page_value.from_plain_text(result.get_sub_name())
        if not self.reading.properties.get(author):
            self.new_properties[author] = author.page_value.from_plain_text(result.get_author())
        if not self.reading.properties.get(publisher):
            self.new_properties[publisher] = publisher.page_value.from_plain_text(result.get_publisher())
        if not self.reading.properties.get(volume):
            self.new_properties[volume] = result.get_page_count()
        if not self.reading.properties.get(cover_image):
            self.new_properties[cover_image] = cover_image.page_value.externals([
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
        title_value = self.reading.properties[title].plain_text
        return self.reading.create_child_page(PageProperties({
            TitleProperty('title'): TitleProperty.page_value.from_plain_text(f'>{title_value}')}))

    def process_lib_gy(self, overwrite: bool) -> bool:
        result = self.gy_scraper.process_page(self.true_name)
        if not result:
            return False
        if overwrite:
            self.reading.properties.pop(location, None)
            self.reading.properties.pop(not_available, None)
        if not self.reading.properties.get(location):
            self.new_properties[location] = location.page_value.from_plain_text(str(result))
            self.new_properties[not_available] = not result.availability
        return True
