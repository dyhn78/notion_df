from __future__ import annotations

from datetime import timezone, timedelta
from typing import Final

my_tz = timezone(timedelta(hours=9))


class _BooleanSettings:
    def __init__(self, default_value: bool):
        self.default: Final[bool] = default_value
        self.enabled = default_value

    def __enter__(self):
        self.enabled = not self.default

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.enabled = self.default

    def __bool__(self):
        return self.enabled


class Settings:
    print_body = _BooleanSettings(False)
