from abc import ABCMeta
from dataclasses import dataclass

from notion_df.object.core import Deserializable, resolve_by_keychain


@resolve_by_keychain('type')
@dataclass
class BlockItem(Deserializable, metaclass=ABCMeta):
    ...
