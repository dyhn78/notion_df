from abc import ABCMeta

from notion_df.resource.core import TypedResource


class PropertySchema(TypedResource, metaclass=ABCMeta):
    ...
