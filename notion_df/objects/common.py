from __future__ import annotations

from datetime import datetime

import dateutil.parser

from notion_df.variables import Variables


def serialize_datetime(dt: datetime):
    return dt.astimezone(Variables.timezone).isoformat()


def deserialize_datetime(serialized: str):
    datetime_obj = dateutil.parser.parse(serialized)
    return datetime_obj.astimezone(Variables.timezone)
