from abc import ABCMeta, abstractmethod
from pprint import pprint


class Editor(metaclass=ABCMeta):
    def __init__(self, root):
        from notion_zap.cli.editors import RootEditor
        self.root: RootEditor = root

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
