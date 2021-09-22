from notion_py.interface.struct import Requestor
from notion_py.interface.gateway.read import RetrievePage
from notion_py.interface.deprecated.parse_deprecated import PageParser
from notion_py.interface.deprecated.write_deprecated import UpdateBasicPage, \
    AppendBlockChildren, UpdateTabularPage
from notion_py.interface.deprecated.write_deprecated.property import BasicPagePropertyStash


class BasicPageDeprecated(Requestor):
    def __bool__(self):
        return True

    def __init__(self, parsed_page: PageParser, parent_id=''):
        self.page_id = parsed_page.page_id
        self.title = parsed_page.title
        if parent_id:
            self.parent_id = parent_id
        else:
            self.parent_id = parsed_page.parent_id

        self._update_props = UpdateBasicPage(parsed_page.page_id)
        self.props: BasicPagePropertyStash = self._update_props.props
        self.props.fetch(parsed_page.props)

        self._append_blocks = AppendBlockChildren(self.page_id)
        self.children = self._append_blocks.children

    @classmethod
    def retrieve(cls, page_id):
        response = RetrievePage(page_id).execute()
        parsed_page = PageParser.from_retrieve_response(response)
        return cls(parsed_page)

    def unpack(self):
        return [self._update_props.unpack(), self._append_blocks.unpack()]

    def execute(self):
        print(self.unpack())
        return [self._update_props.execute(), self._append_blocks.execute()]


class TabularPageDeprecated(BasicPageDeprecated):
    def __bool__(self):
        return True

    PROP_NAME: dict[str, str] = {}

    def __init__(self, parsed_page: PageParser, prop_name: dict[str, str], parent_id=''):
        super().__init__(parsed_page, parent_id=parent_id)
        self.prop_name = prop_name
        self._update_props = UpdateTabularPage(self.page_id)
        self.props = self._update_props.props
        self.props.fetch_children(parsed_page.props)

    @classmethod
    def retrieve(cls, page_id):
        response = RetrievePage(page_id).execute()
        parsed_page = PageParser.from_retrieve_response(response)
        return cls(parsed_page, {})
