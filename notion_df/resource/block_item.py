from abc import ABCMeta
from dataclasses import dataclass

from notion_df.resource.core import Deserializable, set_master


@set_master('type')
@dataclass
class BlockItem(Deserializable, metaclass=ABCMeta):
    ...
