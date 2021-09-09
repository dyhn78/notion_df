from ..twofold_stash import TwofoldListStash
from .unit import WriteTextBlock


class BlockChildrenStash(TwofoldListStash):
    def __init__(self):
        super().__init__()
        self.write = BlockChildPlainAgent(self)
        self.write_rich = BlockChildAgent(self)
        self._overwrite = False

    def unpack(self):
        return {'children': self._unpack()}

    def set_overwrite(self, value: bool):
        """True: 'append'; False: 'write'"""
        self._overwrite = value


class BlockChildPlainAgent:
    def __init__(self, caller: BlockChildrenStash):
        self.caller = caller

    def paragraph(self, text_contents):
        return self.caller.stash(WriteTextBlock('paragraph', text_contents))

    def heading_1(self, text_contents):
        return self.caller.stash(WriteTextBlock('heading_1', text_contents))

    def heading_2(self, text_contents):
        return self.caller.stash(WriteTextBlock('heading_2', text_contents))

    def heading_3(self, text_contents):
        return self.caller.stash(WriteTextBlock('heading_3', text_contents))

    def bulleted_list(self, text_contents):
        return self.caller.stash(WriteTextBlock('bulleted_list_item', text_contents))

    def numbered_list(self, text_contents):
        return self.caller.stash(WriteTextBlock('numbered_list_item', text_contents))

    def to_do(self, text_contents, checked=False):
        return self.caller.stash(WriteTextBlock('to_do', text_contents, checked=checked))

    def toggle(self, text_contents):
        return self.caller.stash(WriteTextBlock('toggle', text_contents))


class BlockChildAgent:
    def __init__(self, caller: BlockChildrenStash):
        self.caller = caller

    def paragraph(self):
        return self.caller.stash(WriteTextBlock('paragraph'))

    def heading_1(self):
        return self.caller.stash(WriteTextBlock('heading_1'))

    def heading_2(self):
        return self.caller.stash(WriteTextBlock('heading_2'))

    def heading_3(self):
        return self.caller.stash(WriteTextBlock('heading_3'))

    def bulleted_list(self):
        return self.caller.stash(WriteTextBlock('bulleted_list_item'))

    def numbered_list(self):
        return self.caller.stash(WriteTextBlock('numbered_list_item'))

    def to_do(self, checked=False):
        return self.caller.stash(WriteTextBlock('to_do', checked=checked))

    def toggle(self):
        return self.caller.stash(WriteTextBlock('toggle'))
