from abc import ABCMeta
from dataclasses import dataclass

from notion_df.resource.core import Deserializable, set_master, resolve_by_keychain


@resolve_by_keychain('type')
@dataclass
class User(Deserializable, metaclass=ABCMeta):
    ...  # TODO
