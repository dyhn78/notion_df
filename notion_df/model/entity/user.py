from abc import ABCMeta
from dataclasses import dataclass

from notion_df.response.core import DualSerializable, resolve_by_keychain


@resolve_by_keychain('type')
@dataclass
class User(DualSerializable, metaclass=ABCMeta):
    ...  # TODO
