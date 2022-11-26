from abc import ABCMeta

from notion_df.util.mixin import Dictable


class PropertySchema(Dictable, metaclass=ABCMeta):
    ...
