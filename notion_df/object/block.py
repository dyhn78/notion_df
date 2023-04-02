from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

from notion_df.object.core import Deserializable, resolve_by_keychain


@resolve_by_keychain('type')
@dataclass
class Block(Deserializable, metaclass=ABCMeta):
    def _plain_serialize(self) -> dict[str, Any]:
        ...
