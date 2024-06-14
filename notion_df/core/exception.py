from __future__ import annotations

from abc import ABC


class NotionDfException(Exception, ABC):
    """The base exception class."""
    pass


class ImplementationError(NotionDfException):
    """Invalid subclass implementation.
     If the error belongs to the notion_df package itself, please raise an issue."""
    pass
