from datetime import datetime
from typing import Final

import dateutil.parser
import pytz


class DateTimeParser:
    def __init__(self, local_timezone: pytz.timezone = pytz.utc):
        self.local_timezone: Final = local_timezone

    def __call__(self, time_string: str) -> datetime:
        datetime_obj = dateutil.parser.parse(time_string)
        return datetime_obj.astimezone(self.local_timezone)


parse_datetime = DateTimeParser()
