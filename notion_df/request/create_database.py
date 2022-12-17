from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from notion_df.request.core import Serializable, Request, RequestSettings
from notion_df.resource.common import RichText, File, Icon
from notion_df.resource.schema import PropertySchema


@dataclass
class DatabaseResponse(Serializable):
    id: str
    created_time_iso: str
    last_edited_time_iso: str
    icon: Icon

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_time": self.created_time_iso,
            "last_edited_time": self.last_edited_time_iso,
            "icon": self.icon,
            "cover": {
                "type": "external",
                "external": {
                    "url": "https://website.domain/images/image.png"
                }
            },
            "url": "https://www.notion.so/bc1211cae3f14939ae34260b16f627c",
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "Grocery List",
                        "link": None
                    },
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default"
                    },
                    "plain_text": "Grocery List",
                    "href": None
                }
            ],
            "properties": {
                "+1": {
                    "id": "Wp%3DC",
                    "name": "+1",
                    "type": "people",
                    "people": {}
                },
                "In stock": {
                    "id": "fk%5EY",
                    "name": "In stock",
                    "type": "checkbox",
                    "checkbox": {}
                },
                "Price": {
                    "id": "evWq",
                    "name": "Price",
                    "type": "number",
                    "number": {
                        "format": "dollar"
                    }
                },
                "Description": {
                    "id": "V}lX",
                    "name": "Description",
                    "type": "rich_text",
                    "rich_text": {}
                },
                "Last ordered": {
                    "id": "eVnV",
                    "name": "Last ordered",
                    "type": "date",
                    "date": {}
                },
                "Meals": {
                    "id": "%7DWA~",
                    "name": "Meals",
                    "type": "relation",
                    "relation": {
                        "database_id": "668d797c-76fa-4934-9b05-ad288df2d136",
                        "single_property": {}
                    }
                },
                "Number of meals": {
                    "id": "Z\\Eh",
                    "name": "Number of meals",
                    "type": "rollup",
                    "rollup": {
                        "rollup_property_name": "Name",
                        "relation_property_name": "Meals",
                        "rollup_property_id": "title",
                        "relation_property_id": "mxp^",
                        "function": "count"
                    }
                },
                "Store availability": {
                    "id": "s}Kq",
                    "name": "Store availability",
                    "type": "multi_select",
                    "multi_select": {
                        "options": [
                            {
                                "id": "cb79b393-d1c1-4528-b517-c450859de766",
                                "name": "Duc Loi Market",
                                "color": "blue"
                            },
                            {
                                "id": "58aae162-75d4-403b-a793-3bc7308e4cd2",
                                "name": "Rainbow Grocery",
                                "color": "gray"
                            },
                            {
                                "id": "22d0f199-babc-44ff-bd80-a9eae3e3fcbf",
                                "name": "Nijiya Market",
                                "color": "purple"
                            },
                            {
                                "id": "0d069987-ffb0-4347-bde2-8e4068003dbc",
                                "name": "Gus's Community Market",
                                "color": "yellow"
                            }
                        ]
                    }
                },
                "Photo": {
                    "id": "yfiK",
                    "name": "Photo",
                    "type": "files",
                    "files": {}
                },
                "Food group": {
                    "id": "CM%3EH",
                    "name": "Food group",
                    "type": "select",
                    "select": {
                        "options": [
                            {
                                "id": "6d4523fa-88cb-4ffd-9364-1e39d0f4e566",
                                "name": "🥦Vegetable",
                                "color": "green"
                            },
                            {
                                "id": "268d7e75-de8f-4c4b-8b9d-de0f97021833",
                                "name": "🍎Fruit",
                                "color": "red"
                            },
                            {
                                "id": "1b234a00-dc97-489c-b987-829264cfdfef",
                                "name": "💪Protein",
                                "color": "yellow"
                            }
                        ]
                    }
                },
                "Name": {
                    "id": "title",
                    "name": "Name",
                    "type": "title",
                    "title": {}
                }
            },
            "parent": {
                "type": "page_id",
                "page_id": "98ad959b-2b6a-4774-80ee-00246fb0ea9b"
            },
            "archived": False
        }

    # def __init__(self, data: dict[str, Any]):
    #     self.id = data['id']
    #     self.created_time = parse_datetime(data['created_time'])
    #     self.icon = ...  # TODO: first implement Resource.deserialize()
    #
    #     self.parent_id_type = data['parent']['type']
    #     self.parent_id = data['parent'][self.parent_id_type]
    #     self.archived = data['archived']

    # @classmethod
    # def from_raw_data(cls, data: dict[str, Any]) -> Self:
    #     pass


@dataclass
class CreateDatabaseRequest(Request[DatabaseResponse]):
    """https://developers.notion.com/reference/create-a-database"""
    parent_id: str
    icon: Icon
    cover: File
    title: list[RichText]
    properties: dict[str, PropertySchema]  # TODO: make this a list

    @classmethod
    def get_settings(cls) -> RequestSettings:
        return RequestSettings(
            notion_version='2022-06-28',
            endpoint='https://api.notion.com/v1/databases/',
            method='POST',
        )

    def get_path(self) -> str:
        return ''

    def get_body(self) -> dict:
        return {
            "parent": {
                "type": "page_id",
                "page_id": self.parent_id
            },
            "icon": self.icon.serialize(),
            "cover": self.cover.serialize(),
            "title": [rich_text.serialize() for rich_text in self.title],
            "properties": {name: schema.serialize() for name, schema in self.properties.items()}
        }
