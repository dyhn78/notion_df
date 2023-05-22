from functools import cached_property
from typing import Optional, Callable, Any, Iterable

from notion_df.entity import Page, Database, Children
from notion_df.object.block import ChildPageBlockValue
from notion_df.object.common import SelectOption
from notion_df.object.filter import CompoundFilter
from notion_df.object.property import SelectProperty, CheckboxFormulaProperty, TitleProperty, RichTextProperty, \
    URLProperty, NumberProperty, FilesProperty, CheckboxProperty, PageProperties
from notion_df.util.collection import StrEnum
from workflow.action.action_core import Action
from workflow.constant.block_enum import DatabaseEnum
from workflow.service.gy_lib_service import GYLibraryScraper, LibraryScrapResult
from workflow.service.webdriver_service import WebDriverFactory
from workflow.service.yes24_service import get_yes24_detail_page_url, Yes24ScrapResult, get_block_value_of_contents_line

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


class MediaScraper(Action):
    def __init__(self, create_window: bool):
        self.reading_db = Database(DatabaseEnum.reading_db.id)
        self.driver_factory = WebDriverFactory(create_window=create_window)

    @cached_property
    def driver(self):
        return self.driver_factory()

    def query_all(self) -> Children[Page]:
        return self.reading_db.query(is_book.filter.equals(True) & CompoundFilter('or', [
            edit_status.filter.equals(option) for option in
            [EditStatusValue.default, EditStatusValue.metadata_overwrite, EditStatusValue.location_overwrite, None]
        ]))

    def filter(self, page: Page) -> bool:
        return (page.parent == self.reading_db and
                (page.properties[edit_status] in
                 [EditStatusValue.default, EditStatusValue.metadata_overwrite, EditStatusValue.location_overwrite]
                 or page.properties[edit_status] is None))

    def process(self, pages: Iterable[Page]):
        for reading in pages:
            ReadingMediaScraperUnit(self, reading).execute()


class ReadingMediaScraperUnit:
    def __init__(self, action: MediaScraper, reading: Page):
        self.action = action
        self.driver = action.driver

        self.reading = reading
        self.new_properties = PageProperties()
        self.callables: list[Callable[[], Any]] = []

        self.title_value = self.extract_title(self.reading.properties[title].plain_text)
        self.true_name_value = self.reading.properties[true_name].plain_text

    def extract_title(self, title_value: str) -> str:
        if title_value.find('_ ') != -1:
            return title_value.split('_ ')[1]
        if title_value.find(' _') != -1:
            true_title_value, author_value = title_value.split(' _', maxsplit=1)
            self.new_properties[title] = \
                RichTextProperty.page_value.from_plain_text(f'{author_value}_ {true_title_value}')
            return true_title_value
        return title_value

    def execute(self) -> None:
        new_status_value = EditStatusValue.fill_manually
        match getattr(self.reading.properties[edit_status], 'name', EditStatusValue.default):
            case EditStatusValue.default:
                if self.process_yes24(False) and self.process_lib_gy(False):
                    new_status_value = EditStatusValue.confirm_manually
            case EditStatusValue.metadata_overwrite:
                if self.process_yes24(True):
                    new_status_value = EditStatusValue.complete
            case EditStatusValue.location_overwrite:
                if self.process_lib_gy(True):
                    new_status_value = EditStatusValue.complete
        self.new_properties[edit_status] = SelectOption(new_status_value)
        self.reading.update(self.new_properties)
        for _callable in self.callables:
            _callable()

    def process_yes24(self, overwrite: bool) -> bool:
        def get_url() -> Optional[str]:
            if url_value := self.reading.properties[url]:
                return url_value
            if url_value := get_yes24_detail_page_url(self.true_name_value):
                self.new_properties[url] = url_value
                return url_value
            if url_value := get_yes24_detail_page_url(self.title_value):
                self.new_properties[url] = url_value
                return url_value

        detail_page_url = get_url()
        if not detail_page_url:
            return False
        result = Yes24ScrapResult.scrap(detail_page_url)

        if result.get_true_name():
            self.true_name_value = result.get_true_name()

        new_properties: PageProperties = PageProperties({
            true_name: true_name.page_value.from_plain_text(result.get_true_name()),
            sub_name: sub_name.page_value.from_plain_text(result.get_sub_name()),
            author: author.page_value.from_plain_text(result.get_author()),
            publisher: publisher.page_value.from_plain_text(result.get_publisher()),
            volume: result.get_page_count(),
        })
        if result.get_cover_image_url():
            new_properties[cover_image] = cover_image.page_value.externals([
                (result.get_cover_image_url(), self.title_value)])
        if not overwrite:
            new_properties = PageProperties({prop: prop_value for prop, prop_value in new_properties.items()
                                             if self.reading.properties.get(prop)})
        self.new_properties.update(new_properties)

        # postpone the edit of content page blocks AFTER the main page's properties
        def set_content_page():
            def get_content_page() -> Optional[Page]:
                for block in self.reading.as_block().retrieve_children():
                    if isinstance(block.value, ChildPageBlockValue):
                        block_title = block.value.title
                        if self.title_value in block_title or block_title.strip() in ['', '=', '>']:
                            _content_page = Page(block.id)
                            _content_page.update(content_page_properties)
                            return _content_page

            content_page_properties = PageProperties({
                TitleProperty('title'): TitleProperty.page_value.from_plain_text(f'>{self.title_value}')})
            content_page = get_content_page()
            if content_page and overwrite:
                content_page.update(archived=True)
                content_page = None
            if not content_page:
                content_page = self.reading.create_child_page(content_page_properties)

            child_values = [get_block_value_of_contents_line(content_line) for content_line in result.get_contents()]
            content_page.as_block().append_children(child_values)

        self.callables.append(set_content_page)
        return True

    def process_lib_gy(self, overwrite: bool) -> bool:
        def get_result() -> Optional[LibraryScrapResult]:
            unit = GYLibraryScraper(self.driver, self.true_name_value, 'gajwa')
            if result := unit.execute():
                return result
            unit = GYLibraryScraper(self.driver, self.title_value, 'gajwa')
            if result := unit.execute():
                return result
            unit = GYLibraryScraper(self.driver, self.true_name_value, 'all_libs')
            if result := unit.execute():
                return result
            unit = GYLibraryScraper(self.driver, self.title_value, 'all_libs')
            if result := unit.execute():
                return result

        scrap_result = get_result()
        if scrap_result is None:
            return False
        if overwrite:
            self.reading.properties.pop(location, None)
            self.reading.properties.pop(not_available, None)
        if not self.reading.properties.get(location):
            self.new_properties[location] = location.page_value.from_plain_text(str(scrap_result))
            self.new_properties[not_available] = not scrap_result.available
        return True
