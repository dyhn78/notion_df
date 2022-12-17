from dataclasses import dataclass
from datetime import datetime

from typing_extensions import Self

from notion_df.resource.core import Resource


@dataclass
class DatePropertyValue(Resource):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def serialize(self):
        # TODO: utilize ExternalSerializable
        # TODO: check Notion time format
        return {
            'start': self.start.isoformat(),
            'end': self.start.isoformat(),
        }

    @classmethod
    def deserialize(cls, serialized: dict) -> Self:
        return cls(datetime.fromisoformat(serialized['start']),
                   datetime.fromisoformat(serialized['end']))


import inspect

signature = inspect.signature(DatePropertyValue.__init__).parameters
print(signature)
