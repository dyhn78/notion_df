from notion_py.interface.parse import BlockChild
from notion_py.interface.structure import TwofoldListStash
from notion_py.interface.write.block_unit import TextBlock, Block


class BlockChildrenStack(TwofoldListStash):
    def __init__(self, edit_mode: str = 'a', read: list[BlockChild] = None):
        super().__init__()
        self.read = read
        self.edit_mode = edit_mode

    def update_read(self, value: list[BlockChild]):
        self.read = value

    def apply(self):
        return {'children': self._unpack()}

    @property
    def write(self):
        return PlainBlockChildAgent(self)

    @property
    def write_rich(self):
        return BlockChildAgent(self)

    # TODO: 향후 block children을 수정, 삭제하는 기능이 추가되면,
    #  'will_overwrite' 메소드와 'conditional_stash' 기능을 추가.
    #  PropertyStack 에서 복붙해오기.


class PlainBlockChildAgent:
    def __init__(self, caller: BlockChildrenStack):
        self.caller = caller

    def page(self, title):
        return self.caller.stash(Block.page(title))

    def paragraph(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'paragraph'))

    def heading_1(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_1'))

    def heading_2(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_2'))

    def heading_3(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_3'))

    def bulleted_list(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'bulleted_list_item'))

    def numbered_list(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'numbered_list_item'))

    def to_do(self, text_content, checked=False):
        return self.caller.stash(TextBlock.plain_form(text_content, 'to_do', checked=checked))

    def toggle(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'toggle'))


class BlockChildAgent:
    def __init__(self, caller: BlockChildrenStack):
        self.caller = caller

    def paragraph(self):
        return self.caller.stash(TextBlock('paragraph'))

    def heading_1(self):
        return self.caller.stash(TextBlock('heading_1'))

    def heading_2(self):
        return self.caller.stash(TextBlock('heading_2'))

    def heading_3(self):
        return self.caller.stash(TextBlock('heading_3'))

    def bulleted_list(self):
        return self.caller.stash(TextBlock('bulleted_list_item'))

    def numbered_list(self):
        return self.caller.stash(TextBlock('numbered_list_item'))

    def to_do(self, checked=False):
        return self.caller.stash(TextBlock('to_do', checked=checked))

    def toggle(self):
        return self.caller.stash(TextBlock('toggle'))
