from abc import ABCMeta

from notion_df.resource.core import UniqueResource


class PropertySchema(UniqueResource, metaclass=ABCMeta):
    ...
