from dataclasses import dataclass
from datetime import datetime

from notion_df.resource.core import Resource


@dataclass
class DatePropertyValue(Resource):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def serialize(self):
        return {
            'start': self.start,
            'end': self.end,
        }
