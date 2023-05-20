from __future__ import annotations

from datetime import timezone, timedelta
from typing import Final

my_tz = timezone(timedelta(hours=9))


class BooleanSettings:
    def __init__(self, default_value: bool):
        self.default: Final[bool] = default_value
        self.enabled = default_value

    def __enter__(self):
        self.enabled = not self.default

    def __exit__(self):
        self.enabled = self.default

    def __bool__(self):
        return self.enabled


settings_print_body = BooleanSettings(False)
