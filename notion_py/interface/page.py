from typing import Optional, Any

from notion_py.interface.get.property import PropertyFrame
from .parse import PageParser
from ..gateway.common import Requestor
from ..gateway.write import UpdateTabularPage, UpdateBasicPage, \
    AppendBlockChildren


class TabularPage(Requestor):
    def __init__(self, page_id: str, title: str,
                 frame: Optional[PropertyFrame] = None,
                 prop_plain: Optional[dict[str, Any]] = None,
                 prop_rich: Optional[dict[str, Any]] = None):
        self.props = TabularPageProps(page_id, prop_plain, prop_rich)
        self.blocks = self.requests['blocks'].children.write
        self.requests = {'props': self.props.requests,
                         'blocks': self.blocks.requests}
        self.set_overwrite_option(True)

        self.title = title
        if frame is None:
            frame = PropertyFrame()

    def apply(self):
        return {key: value.apply() for key, value in self.requests}

    def execute(self):
        return {key: value.execute() for key, value in self.requests}

    def set_overwrite_option(self, option: bool):
        self.props.overwrite_option = option


class TabularPageProps(Requestor):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 prop_plain: Optional[dict[str, Any]] = None,
                 prop_rich: Optional[dict[str, Any]] = None):
        self.requests = UpdateTabularPage(page_id)
        self.write = self.requests.props.write
        self.overwrite_option = True

        self.frame = frame
        self._read_full = {}
        self._read_rich = prop_rich
        self._read_plain = prop_plain
        for prop_name in prop_plain:
            if prop_name in prop_rich:
                value = {'plain': prop_plain[prop_name],
                         'rich': prop_rich[prop_name]}
            else:
                value = prop_plain[prop_name]
            self._read_full[prop_name] = value

    def apply(self):
        pass

    def execute(self):
        pass

    def read_all(self):
        return self._read_full

    def read_all_keys(self):
        return {key: self._read_full[self.prop_name(key)] for key in self.frame}

    def read(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich(self, prop_name: str):
        return self._read_rich[prop_name]

    def prop_name(self, prop_key):
        return self.frame[prop_key].name

    def read_on(self, prop_key: str):
        return self._read_plain[self.prop_name(prop_key)]

    def read_rich_on(self, prop_key: str):
        return self._read_rich[self.prop_name(prop_key)]

    @classmethod
    def read_empty(cls, value):
        if type(value) in [bool, list, dict]:
            return bool(value)
        else:
            return str(value) in ['', '.', '-', '0', '1']


class TabularPageBlocks(Requestor):
    def __init__(self, block_plain, block_rich):
        self._read_plain = block_plain
        self._read_rich = block_rich

    def apply(self):
        pass

    def execute(self):
        pass


class BasicPage(Requestor):
    def __init__(self, retrieve_response: dict,
                 page_id: Optional[str]):
        page_parser = PageParser.fetch_retrieve(retrieve_response)
        self.request = {}
        if page_id:
            self.request.update(update=UpdateBasicPage(page_id))

    def apply(self):
        pass

    def execute(self):
        pass

    def read_title(self):
        pass

    def read_rich_title(self):
        pass

    def write_title(self):
        pass

    def write_rich_title(self):
        pass
