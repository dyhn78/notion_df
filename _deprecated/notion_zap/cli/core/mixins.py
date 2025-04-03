from abc import ABCMeta, abstractmethod, ABC
from pprint import pprint


class Saveable(metaclass=ABCMeta):
    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def save_info(self):
        pass

    @abstractmethod
    def save_required(self) -> bool:
        pass

    def save_preview(self, **kwargs):
        pprint(self.save_info(), **kwargs)


class Printable(ABC):
    @abstractmethod
    def preview(self, **kwargs):
        pass


class Executable(Printable, metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        pass


class ValueCarrier(Printable, metaclass=ABCMeta):
    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def encode(self):
        pass

    def preview(self, **kwargs):
        try:
            pprint(self.encode(), **kwargs)
        except AttributeError:
            pass