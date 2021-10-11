from abc import ABCMeta

from notion_py.interface.editor.struct import MasterEditor, PointEditor


class SupportedBlock(MasterEditor, metaclass=ABCMeta):
    @classmethod
    def create_new(cls, caller: PointEditor):
        return cls(caller, '')
