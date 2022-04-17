from enum import Enum

from notion_zap.apps.constants import EmojiCode


class MyBlock(Enum):
    def __new__(cls, title: str, id_or_url: str, prefix=''):
        obj = object.__new__(cls)
        obj._value_ = title
        obj.title = title
        obj.id_or_url = id_or_url
        obj.prefix = prefix
        return obj

    @property
    def prefix_title(self):
        return self.prefix + self.title

    systems = ('체계', '69b4e661c4ee43b6a5e40c8b28e6f9d1', EmojiCode.GLOBE_ASIA)

    journals = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d', EmojiCode.PURPLE_CIRCLE)
    counts = ('진도', 'c8d46c01d6c941a9bf8df5d115a05f03', EmojiCode.PURPLE_HEART)
    topics = ('발전', 'fa7d93f6fbd341f089b185745c834811', EmojiCode.BLUE_CIRCLE)
    streams = ('조류', 'e8782fe4e1a34c9d846d57b01a370327', EmojiCode.BLUE_HEART)
    readings = ('읽기', 'c326f77425a0446a8aa309478767c85b', EmojiCode.YELLOW_CIRCLE)
    writings = ('쓰기', '069bbebd632f4a6ea3044575a064cf0f', EmojiCode.YELLOW_HEART)

    weeks = ('주간', 'd020b399cf5947a59d11a0b9e0ea45d0', EmojiCode.GREEN_CIRCLE)
    dates = ('일간', '961d1ca0a3d24a46b838ba85e710f18d', EmojiCode.GREEN_HEART)
    projects = ('실행', 'eb2f09a1de41412e8b2357bc04f26e74', EmojiCode.RED_HEART)
    domains = ('꼭지', '2c5411ba6a0f43a0a8aa06295751e37a', EmojiCode.RED_CIRCLE)
    channels = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86', EmojiCode.ORANGE_CIRCLE)
    people = ('인물', '3c08cdba5a044e9c9b7e31ee8509f506', EmojiCode.ORANGE_HEART)
    locations = ('장소', '920e2e10225d450d8bb084697f6d0fc6', EmojiCode.ORANGE_DIAMOND)


class DatabaseInfoDepr:
    """(database_alias, database_id)"""
    JOURNALS = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d')
    CHECKS = ('진도', 'c8d46c01d6c941a9bf8df5d115a05f03')
    TOPICS = ('발전', 'fa7d93f6fbd341f089b185745c834811')
    TASKS = ('조류', 'e8782fe4e1a34c9d846d57b01a370327')
    READINGS = ('읽기', 'c326f77425a0446a8aa309478767c85b')
    WRITINGS = ('쓰기', '069bbebd632f4a6ea3044575a064cf0f')

    PERIODS = ('주간', 'd020b399cf5947a59d11a0b9e0ea45d0')
    DATES = ('일간', '961d1ca0a3d24a46b838ba85e710f18d')
    PROJECTS = ('실행', 'eb2f09a1de41412e8b2357bc04f26e74')
    DOMAINS = ('꼭지', '2c5411ba6a0f43a0a8aa06295751e37a')
    CHANNELS = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86')


if __name__ == '__main__':
    from notion_zap.cli.utility.page_id_to_url import id_to_url

    print(id_to_url(DatabaseInfoDepr.JOURNALS[1]))
