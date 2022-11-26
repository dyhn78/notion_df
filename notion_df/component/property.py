from dataclasses import dataclass
from datetime import datetime

from notion_df.util.mixin import Dictable


@dataclass
class DatePropertyValue(Dictable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def to_dict(self) -> dict[str, str]:
        return {
            'start': self.start.isoformat(),  # TODO: check Notion time format
            'end': self.start.isoformat(),
        }
