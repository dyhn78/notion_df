from abc import ABCMeta
from dataclasses import dataclass

from notion_df.resource.core import Deserializable, master


@master
@dataclass
class User(Deserializable, metaclass=ABCMeta):
    ...  # TODO
