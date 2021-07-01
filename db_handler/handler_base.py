from abc import abstractmethod, ABC


class BaseHandler(ABC):
    @property
    @abstractmethod
    def apply(self):
        pass


class RequestHandler(BaseHandler):
    @property
    @abstractmethod
    def apply(self):
        pass
