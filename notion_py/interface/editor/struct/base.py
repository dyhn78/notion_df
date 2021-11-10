from abc import ABCMeta, abstractmethod
from pprint import pprint


class Editor(metaclass=ABCMeta):
    def __init__(self, root_editor):
        from notion_py.interface.editor import RootEditor
        self.root: RootEditor = root_editor

    @abstractmethod
    def save_required(self) -> bool:
        pass

    @abstractmethod
    def save_info(self):
        pass

    def save_preview(self, **kwargs):
        pprint(self.save_info(), **kwargs)

    @abstractmethod
    def save(self):
        pass
