from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotionDfException(Exception, ABC):
    """the base exception class, defined with dataclass style.

    - __doc__: class-level description
    - description: instance-specific description
    - vars: dumped variables to display in error log
    """
    description: str = field(default='')
    """instance-specific description"""
    vars: dict[str, Any] = field(default_factory=dict)
    """dumped variables in error log"""
    linebreak: bool = field(default=False, kw_only=True)
    """whether or not to print one variable at a line"""

    def __init_subclass__(cls, **kwargs):
        dataclass(cls)

    def __post_init__(self):
        self.args: tuple[str, ...] = ()
        if self.description:
            self.args += self.description,
        var_items_list = [f'{k} = {v}' for k, v in self.vars.items()]
        if self.linebreak:
            var_items_str = '[[\n' + '\n'.join(var_items_list) + '\n]]'
        else:
            var_items_str = '[[ ' + ', '.join(var_items_list) + ' ]]'
        self.args += var_items_str,


class NotionDfKeyError(NotionDfException, KeyError):
    pass


class NotionDfValueError(NotionDfException, ValueError):
    pass


class NotionDfTypeError(NotionDfException, TypeError):
    pass


class NotionDfNotImplementedError(NotionDfException, NotImplementedError):
    pass


class NotionDfAttributeError(NotionDfException, AttributeError):
    pass


class NotionDfStateError(NotionDfException):
    """invalid state is detected."""
