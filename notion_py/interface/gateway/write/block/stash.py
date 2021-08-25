from abc import ABCMeta

from notion_py.interface.common import TwofoldStash, ValueCarrier
from .unit import TextBlockWriter


class TwofoldListStash(TwofoldStash, metaclass=ABCMeta):
    def _unpack(self):
        return [carrier.unpack() for carrier in self._subcarriers]

    def apply_left(self, carrier: ValueCarrier):
        self._subcarriers.insert(0, carrier)
        return self._subcarriers[0]


class BlockChildrenStash(TwofoldListStash):
    # TODO: 향후 block children을 수정, 삭제하는 기능이 추가되면,
    #  'will_overwrite' 메소드와 'conditional_stash' 기능을 추가.
    #  PropertyStack 에서 복붙해오기.

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
        return self.caller.apply(TextBlockWriter('paragraph').write_text(text_contents))

    def heading_1(self, text_contents):
        return self.caller.apply(TextBlockWriter('heading_1').write_text(text_contents))

    def heading_2(self, text_contents):
        return self.caller.apply(TextBlockWriter('heading_2').write_text(text_contents))

    def heading_3(self, text_contents):
        return self.caller.apply(TextBlockWriter('heading_3').write_text(text_contents))

    def bulleted_list(self, text_contents):
        return self.caller.apply(
            TextBlockWriter('bulleted_list_item').write_text(text_contents))

    def numbered_list(self, text_contents):
        return self.caller.apply(
            TextBlockWriter('numbered_list_item').write_text(text_contents))

    def to_do(self, text_contents, checked=False):
        return self.caller.apply(
            TextBlockWriter('to_do', checked=checked).write_text(text_contents))

    def toggle(self, text_contents):
        return self.caller.apply(TextBlockWriter('toggle').write_text(text_contents))


class BlockChildAgent:
    def __init__(self, caller: BlockChildrenStash):
        self.caller = caller

    def paragraph(self):
        return self.caller.apply(TextBlockWriter('paragraph'))

    def heading_1(self):
        return self.caller.apply(TextBlockWriter('heading_1'))

    def heading_2(self):
        return self.caller.apply(TextBlockWriter('heading_2'))

    def heading_3(self):
        return self.caller.apply(TextBlockWriter('heading_3'))

    def bulleted_list(self):
        return self.caller.apply(TextBlockWriter('bulleted_list_item'))

    def numbered_list(self):
        return self.caller.apply(TextBlockWriter('numbered_list_item'))

    def to_do(self, checked=False):
        return self.caller.apply(TextBlockWriter('to_do', checked=checked))

    def toggle(self):
        return self.caller.apply(TextBlockWriter('toggle'))
