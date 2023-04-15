from abc import ABCMeta
from dataclasses import dataclass

from notion_df.object.core import DualSerializable


@dataclass
class User(DualSerializable, metaclass=ABCMeta):
    ...  # TODO
