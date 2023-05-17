from enum import Enum

from notion_df.util.misc import get_id, get_url
from workflow.constant.emoji_code import EmojiCode


class DatabaseEnum(Enum):
    def __init__(self, title: str, id_or_url: str, prefix: str):
        self._value_ = self._name_
        self.title = title
        self.id = get_id(id_or_url)
        self.url = get_url(id_or_url, 'dyhn')
        self.prefix = prefix

    @property
    def prefix_title(self):
        return self.prefix + self.title

    journals = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d', EmojiCode.ORANGE_CIRCLE)
    notes = ('바탕', 'fa7d93f6fbd341f089b185745c834811', EmojiCode.ORANGE_HEART)

    events = ('일과', 'c8d46c01d6c941a9bf8df5d115a05f03', EmojiCode.BLUE_CIRCLE)
    issues = ('진행', 'e8782fe4e1a34c9d846d57b01a370327', EmojiCode.BLUE_HEART)

    readings = ('읽기', 'c326f77425a0446a8aa309478767c85b', EmojiCode.YELLOW_CIRCLE)
    sections = ('부문', '52d387ea0aaa470cb69332708c61b34d', EmojiCode.YELLOW_HEART)

    streams = ('전개', 'eb2f09a1de41412e8b2357bc04f26e74', EmojiCode.RED_CIRCLE)
    agendas = ('마디', '9f21ad86079d4caaa7ed9461a7f37288', EmojiCode.RED_HEART)

    topics = ('주제', '2c5411ba6a0f43a0a8aa06295751e37a', EmojiCode.PURPLE_CIRCLE)
    subjects = ('담론', 'eca1ba6d4831459ca8becc283f1f8c4e', EmojiCode.PURPLE_HEART)

    dates = ('일간', '961d1ca0a3d24a46b838ba85e710f18d', EmojiCode.GREEN_CIRCLE)
    weeks = ('주간', 'd020b399cf5947a59d11a0b9e0ea45d0', EmojiCode.GREEN_HEART)

    # depr_projects = ('활동', '69b4e66c4ee43b6a5e40c8b28e6f9d1', EmojiCode.BLACK_HEART)
    depr_people = ('인물', '3c08cdba5a044e9c9b7e31ee8509f506', EmojiCode.BLACK_HEART)
    depr_channels = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86', EmojiCode.BLACK_HEART)
    depr_locations = ('장소', '920e2e10225d450d8bb084697f6d0fc6', EmojiCode.BLACK_HEART)
    depr_writings = ('표현', '069bbebd632f4a6ea3044575a064cf0f', EmojiCode.BLACK_HEART)
    depr_statuses = ('생활', '52df5fae504b4d35918b03bb82080500', EmojiCode.BLACK_HEART)
    depr_issues = ('주관', '8baa30054f00483a8f0538fd3cd9543a', EmojiCode.BLACK_HEART)
    depr_groups = ('갈래', '679c2515870d46e3a107b42cd2a5ffc3', EmojiCode.BLACK_HEART)
    depr_themes = ('주제', '5464267393e940a58e3f10db306bf3e4', EmojiCode.BLACK_HEART)
