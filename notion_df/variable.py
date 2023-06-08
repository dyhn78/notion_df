from __future__ import annotations

import functools
import os
from abc import abstractmethod, ABCMeta
from datetime import timezone, timedelta
from typing import Final, Callable

my_tz = timezone(timedelta(hours=9))
print_width = 160
token: Final[str] = os.getenv('NOTION_TOKEN')  # TODO: support multiple token


class _Settings(metaclass=ABCMeta):
    def __call__(self, func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                func(*args, **kwargs)

        return wrapper

    @abstractmethod
    def __enter__(self) -> None:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class _BooleanSettings(_Settings):
    def __init__(self, default_value: bool):
        self.default: Final[bool] = default_value
        self.enabled = default_value

    def __enter__(self) -> None:
        self.enabled = not self.default

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.enabled = self.default

    def __bool__(self):
        return self.enabled

    def filter(self, value: bool):
        if value == self.default:
            return _DummySettings()
        else:
            return self


class _DummySettings(_Settings):
    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class Settings:
    print: _BooleanSettings = _BooleanSettings(False)
