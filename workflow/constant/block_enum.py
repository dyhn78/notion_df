from __future__ import annotations

from enum import Enum
from typing import Optional

from notion_df.core.entity_base import Entity
from notion_df.entity import Database
from notion_df.object.common import Emoji
from notion_df.object.rich_text import RichText, TextSpan
from notion_df.util.uuid_util import get_page_or_database_id, get_page_or_database_url
from workflow.constant.emoji_code import EmojiCode

_id_to_member = {}


class DatabaseEnum(Enum):
    event_db = ('일과', 'c8d46c01d6c941a9bf8df5d115a05f03', EmojiCode.BLUE_CIRCLE)
    issue_db = ('줄기', 'e8782fe4e1a34c9d846d57b01a370327', EmojiCode.BLUE_HEART)

    journal_db = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d', EmojiCode.ORANGE_CIRCLE)
    stage_db = ('바탕', 'fa7d93f6fbd341f089b185745c834811', EmojiCode.ORANGE_HEART)

    reading_db = ('읽기', 'c326f77425a0446a8aa309478767c85b', EmojiCode.YELLOW_CIRCLE)
    topic_db = ('분야', '52d387ea0aaa470cb69332708c61b34d', EmojiCode.YELLOW_HEART)

    stream_db = ('진행', 'eb2f09a1de41412e8b2357bc04f26e74', EmojiCode.RED_CIRCLE)
    section_db = ('전개', '9f21ad86079d4caaa7ed9461a7f37288', EmojiCode.RED_HEART)

    point_db = ('꼭지', '2c5411ba6a0f43a0a8aa06295751e37a', EmojiCode.PURPLE_CIRCLE)
    subject_db = ('담론', 'eca1ba6d4831459ca8becc283f1f8c4e', EmojiCode.PURPLE_HEART)

    date_db = ('일간', '961d1ca0a3d24a46b838ba85e710f18d', EmojiCode.GREEN_CIRCLE)
    week_db = ('주간', 'd020b399cf5947a59d11a0b9e0ea45d0', EmojiCode.GREEN_HEART)

    depr_people_db = ('인물', '3c08cdba5a044e9c9b7e31ee8509f506', EmojiCode.BLACK_HEART)
    depr_channel_db = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86', EmojiCode.BLACK_HEART)
    depr_location_db = ('장소', '920e2e10225d450d8bb084697f6d0fc6', EmojiCode.BLACK_HEART)
    depr_writing_db = ('표현', '069bbebd632f4a6ea3044575a064cf0f', EmojiCode.BLACK_HEART)
    depr_theme_db = ('주제 -220222', '5464267393e940a58e3f10db306bf3e4', EmojiCode.BLACK_HEART)

    def __init__(self, title: str, id_or_url: str, prefix: str):
        self._value_ = self._name_
        self.title = title
        self.id = get_page_or_database_id(id_or_url)
        self.url = get_page_or_database_url(id_or_url, 'dyhn')
        self.prefix = prefix
        _id_to_member[Database(self.id)] = self

    @property
    def prefix_title(self):
        return self.prefix + self.title

    @property
    def entity(self) -> Database:
        db = Database(self.id)
        if not hasattr(db, 'title'):
            title_span = TextSpan(self.title)
            title_span.plain_text = self.title
            db.title = RichText([title_span])
        if not hasattr(db, 'icon'):
            db.icon = Emoji(self.prefix)
        return db

    @classmethod
    def from_entity(cls, entity: Entity) -> Optional[DatabaseEnum]:
        return _id_to_member.get(entity)
