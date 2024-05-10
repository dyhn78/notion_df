from __future__ import annotations

from abc import ABC


class NotionDfException(Exception, ABC):
    """the base exception class."""
    pass


class ImplementationError(NotionDfException):
    """invalid subclass implementation. If the error belongs to the package itself, please raise an issue."""
    pass
