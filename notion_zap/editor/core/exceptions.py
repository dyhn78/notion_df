# TODO: think cooler project name
from abc import ABC


class NotionZapException(Exception, ABC):
    """the base exception class."""
    pass


class CircularLabelException(NotionZapException):
    """circular hierarchy between labels detected; in other words, broken DAG."""
    pass
