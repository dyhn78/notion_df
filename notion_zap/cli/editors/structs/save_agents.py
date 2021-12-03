from abc import ABCMeta, abstractmethod

from .base_logic import Saveable
from .block_main import Block, Follower
from notion_zap.cli.gateway.requestors.structs import Requestor


class ListEditor(Follower, Saveable, metaclass=ABCMeta):
    @property
    @abstractmethod
    def values(self) -> list[Block]:
        pass

    def save(self):
        return [child.save() for child in self.values]

    def save_info(self):
        return [child.save_info() for child in self.values]

    def save_required(self):
        return any([child for child in self.values])

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index: int):
        return self.values[index]


class RequestEditor(Follower, Saveable, metaclass=ABCMeta):
    @property
    @abstractmethod
    def requestor(self) -> Requestor:
        pass

    def save(self):
        return self.requestor.execute()

    def save_info(self):
        return self.requestor.encode()

    def save_required(self):
        return self.requestor.__bool__()


class SingularEditor(Follower, Saveable, metaclass=ABCMeta):
    @property
    @abstractmethod
    def value(self) -> Block:
        pass

    def save(self):
        return self.value.save()

    def save_info(self):
        return self.value.save_info()

    def save_required(self):
        return self.value.save_required()
