class DatabaseInfo:
    """(database_alias, database_id)"""
    PERIODS = ('기간', 'd020b399cf5947a59d11a0b9e0ea45d0')
    DATES = ('날짜', '961d1ca0a3d24a46b838ba85e710f18d')

    JOURNALS = ('일지', 'c226cffe6cf84ab996bbc384bf26bf1d')
    CHECKS = ('진도', 'c8d46c01d6c941a9bf8df5d115a05f03')
    TOPICS = ('발전', 'fa7d93f6fbd341f089b185745c834811')
    TASKS = ('조류', 'e8782fe4e1a34c9d846d57b01a370327')
    READINGS = ('읽기', 'c326f77425a0446a8aa309478767c85b')
    WRITINGS = ('쓰기', '069bbebd632f4a6ea3044575a064cf0f')

    PROJECTS = ('실행', 'eb2f09a1de41412e8b2357bc04f26e74')
    DOMAINS = ('꼭지', '2c5411ba6a0f43a0a8aa06295751e37a')
    CHANNELS = ('채널', '2d3f4ea770854b8e9e30abecd4d31a86')


if __name__ == '__main__':
    from notion_zap.cli.utility.page_id_to_url import id_to_url
    print(id_to_url(DatabaseInfo.JOURNALS[1]))
