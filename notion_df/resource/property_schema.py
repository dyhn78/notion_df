from abc import ABCMeta

from notion_df.resource.core import TypedResource


class PropertySchema(TypedResource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-schema-object
    # https://developers.notion.com/reference/update-property-schema-object
    ...
