from abc import ABCMeta

from notion_df.resource import Resource


class PropertySchema(Resource, metaclass=ABCMeta):
    ...
