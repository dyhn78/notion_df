from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar

from notion_df.core.serialization import Deserializable


@dataclass
class Response(Deserializable, metaclass=ABCMeta):
    timestamp: datetime = field(init=False, default_factory=datetime.now)


Response_T = TypeVar('Response_T', bound=Response)
