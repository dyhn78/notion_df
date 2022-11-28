from abc import ABCMeta

from notion_df.util.mixin import DataObject


class PropertySchema(DataObject, metaclass=ABCMeta):
    ...
