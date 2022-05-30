from notion_zap.apps.config import MyBlock
from notion_zap.apps.emoji_code import EmojiCode
from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Column, PropertyMarkedValue as Value


class Columns:
    # basic properties
    title_generic = Column(key=EmojiCode.ORANGE_BOOK + '제목', alias='title')
    title_datetime = Column(key=EmojiCode.GREEN_BOOK + '제목', alias='title')
    title_metadata = Column(key=EmojiCode.BOOKSTACK + '제목', alias='title')

    media_type = Column(key=EmojiCode.BLUE_BOOK + '유형', alias='media_type',
                        marked_values=[Value('📌결정 전', 'empty')])
    media_type_book = Column(alias='is_book', key='📔도서류', )
    no_exp = Column(key=EmojiCode.BLACK_NOTEBOOK + '경험 없음', alias='no_exp', )
    no_exp_book = Column(key=EmojiCode.BLACK_NOTEBOOK + '도서류&경험 없음', alias='no_exp_book', )

    timestr = Column(key=EmojiCode.CALENDAR + '시간', alias='timestr', )
    manual_date = Column(key=EmojiCode.CALENDAR + '날짜', alias='manual_date', )
    manual_date_range = Column(key=EmojiCode.BIG_CALENDAR + '날짜 범위', alias='manual_date', )

    # relational properties
    itself = Column(key=EmojiCode.CYCLE + '재귀', alias='itself', )

    weeks = Column(key=MyBlock.weeks.prefix_title, alias='weeks', )
    dates = Column(key=MyBlock.dates.prefix_title, alias='dates', )
    dates_created = Column(key=MyBlock.dates.prefix + '생성', alias='dates_created', )

    journals = Column(key=MyBlock.journals.prefix_title, alias='journals', )
    checks = Column(key=MyBlock.counts.prefix_title, alias='counts', )

    issues = Column(key=MyBlock.issues.prefix_title, alias='issues', )
    tasks = Column(key=MyBlock.tasks.prefix_title, alias='tasks', )

    readings = Column(key=MyBlock.readings.prefix_title, alias='readings', )
    readings_begin = Column(key=MyBlock.readings.prefix + '시작', alias='readings_begin')
    writings = Column(key=MyBlock.writings.prefix_title, alias='writings', )

    processes = Column(key=MyBlock.processes.prefix_title, alias='processes', )
    processes_main = Column(key=MyBlock.processes.prefix + '중심',
                            aliases=['processes_main', 'processes'])
    processes_side = Column(key=MyBlock.processes.prefix + '주변', alias='processes_side')
    channels = Column(key=MyBlock.channels.prefix_title, alias='channels', )

    domains = Column(key=MyBlock.domains.prefix_title, alias='domains', )
    people = Column(key=MyBlock.people.prefix_title, alias='people', )
    locations = Column(key=MyBlock.locations.prefix_title, alias='locations', )


class SubFrames:
    gcal = Frame([
        Column(alias='gcal_sync_status', key=EmojiCode.YELLOW_NOTEBOOK + '달력'),
        Column(alias='gcal_link', key=EmojiCode.YELLOW_NOTEBOOK + '링크'),
        Column(alias='gcal_id', key=EmojiCode.YELLOW_NOTEBOOK + 'id'),
    ])

    date_auto_created = Frame([
        Column(key=EmojiCode.TIMER + '일시', alias='datetime_auto', ),
        Column(key=EmojiCode.TIMER + '날짜', alias='date_auto', ),
    ])

    dates = Frame([
        Columns.weeks,
        Columns.dates
    ])
    dates_begin = Frame([
        Column(key=MyBlock.weeks.prefix + '시작', aliases=['weeks_begin', 'weeks']),
        Column(key=MyBlock.dates.prefix + '시작', aliases=['dates_begin', 'dates']),
    ])


Frames: dict[MyBlock, Frame] = {
    MyBlock.weeks: Frame(
        [
            Columns.title_datetime,
            Columns.manual_date_range,

            Columns.itself,
        ]
    ),
    MyBlock.dates: Frame(
        [
            Columns.title_datetime, Columns.manual_date,

            Columns.itself,
            Columns.weeks,
            Columns.journals,
            Columns.locations, Columns.channels,
        ]
    ),

    MyBlock.journals: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        SubFrames.gcal,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.itself,
            Columns.processes_main, Columns.processes_side, Columns.domains,
            Columns.channels, Columns.readings,

            Columns.issues, Columns.writings,
        ]
    ),
    MyBlock.counts: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.itself,
            Columns.processes,
            Columns.readings, Columns.writings,
        ]
    ),

    MyBlock.issues: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.journals, Columns.checks,
            Columns.tasks,
            Columns.channels,
            Columns.readings, Columns.writings,
        ]
    ),
    MyBlock.tasks: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.itself,
            Columns.people, Columns.locations, Columns.channels,
            Columns.readings,
        ]
    ),

    MyBlock.readings: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_metadata,
            Columns.media_type,
            Columns.media_type_book,
            Columns.no_exp, Columns.no_exp_book,

            Columns.dates_created,
            Columns.itself,
            Columns.channels,

            Columns.journals, Columns.tasks,
            Columns.checks, Columns.writings,
        ]
    ),
    MyBlock.points: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.itself,
            Columns.journals,
            Columns.readings, Columns.writings,
            Columns.processes, Columns.channels,
            Columns.domains, Columns.people, Columns.locations,
        ]
    ),
    MyBlock.writings: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.readings, Columns.writings,
            Columns.processes, Columns.channels,
            Columns.domains, Columns.people, Columns.locations,
        ]
    ),

    MyBlock.processes: Frame(
        SubFrames.date_auto_created,
        [

        ]
    ),
    MyBlock.channels: Frame(
        [
            Columns.title_metadata,
            Columns.media_type,
            Columns.media_type_book,
        ]
    )
}
