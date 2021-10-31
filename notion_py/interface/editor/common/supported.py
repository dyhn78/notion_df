from abc import ABCMeta

from notion_py.interface.editor.common.struct import MasterEditor, PointEditor


class SupportedBlock(MasterEditor, metaclass=ABCMeta):
    @classmethod
    def create_new(cls, caller: PointEditor):
        return cls(caller, '')

    @property
    def is_supported_type(self) -> bool:
        return True
