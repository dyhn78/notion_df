from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Column, PropertyMarkedValue as Value
from ..config import MyBlock
from ..constants import EmojiCode


class Columns:
    # basic properties
    title_generic = Column(key=EmojiCode.ORANGE_BOOK + '제목', alias='title')
    title_datetime = Column(key=EmojiCode.GREEN_BOOK + '제목', alias='title')
    title_metadata = Column(key=EmojiCode.BOOKSTACK + '제목', alias='title')

    no_exp = Column(key=EmojiCode.BLACK_NOTEBOOK + '경험 없음', alias='no_exp', )

    media_type = Column(key=EmojiCode.BLUE_BOOK + '유형', alias='media_type',
                        marked_values=[Value('📌결정 전', 'empty')])
    media_type_book = Column(alias='is_book', key='📔도서류', )

    timestr = Column(key=EmojiCode.CALENDAR + '시간', alias='timestr', )
    date_manual = Column(key=EmojiCode.CALENDAR + '날짜', alias='date_manual', )
    date_manual_range = Column(key=EmojiCode.BIG_CALENDAR + '날짜 범위',
                               alias='date_manual', )

    # relational properties
    itself = Column(key=EmojiCode.CYCLE + '재귀', alias='itself', )

    weeks = Column(key=MyBlock.weeks.prefix_title, alias='weeks', )
    dates = Column(key=MyBlock.dates.prefix_title, alias='dates', )

    journals = Column(key=MyBlock.journals.prefix_title, alias='journals', )
    checks = Column(key=MyBlock.counts.prefix_title, alias='counts', )

    topics = Column(key=MyBlock.topics.prefix_title, alias='topics', )
    streams = Column(key=MyBlock.streams.prefix_title, alias='streams', )

    readings = Column(key=MyBlock.readings.prefix_title, alias='readings', )
    readings_begin = Column(key=MyBlock.readings.prefix + '시작', alias='readings_begin')
    writings = Column(key=MyBlock.writings.prefix_title, alias='writings', )

    projects = Column(key=MyBlock.projects.prefix_title, alias='projects', )
    projects_main = Column(key=MyBlock.projects.prefix + '중심',
                           aliases=['projects_main', 'projects'])
    projects_side = Column(key=MyBlock.projects.prefix + '주변', alias='projects_side')
    domains = Column(key=MyBlock.domains.prefix_title, alias='domains', )

    channels = Column(key=MyBlock.channels.prefix_title, alias='channels', )
    people = Column(key=MyBlock.people.prefix_title, alias='people', )
    locations = Column(key=MyBlock.locations.prefix_title, alias='locations', )


class SubFrames:
    gcal = Frame([
        Column(alias='gcal_sync_status', key=EmojiCode.YELLOW_NOTEBOOK + '달력'),
        Column(alias='gcal_link', key=EmojiCode.YELLOW_NOTEBOOK + '링크'),
        Column(alias='gcal_id', key=EmojiCode.YELLOW_NOTEBOOK + 'id'),
    ])

    dateval_created = Frame([
        Column(key=EmojiCode.TIMER + '일시', alias='auto_datetime', ),
        Column(key=EmojiCode.TIMER + '날짜', alias='auto_date', ),
    ])

    dates = Frame([
        Columns.weeks,
        Columns.dates
    ])
    dates_begin = Frame([
        Column(key=MyBlock.weeks.prefix + '시작', aliases=['periods_begin', 'weeks']),
        Column(key=MyBlock.dates.prefix + '시작', aliases=['dates_begin', 'dates']),
    ])
    dates_created = Frame([
        Column(key=MyBlock.weeks.prefix + '생성', alias='periods_created', ),
        Column(key=MyBlock.dates.prefix + '생성', alias='dates_created', )
    ])


Frames: dict[MyBlock, Frame] = {
    MyBlock.journals: Frame(
        SubFrames.dateval_created, SubFrames.dates, SubFrames.dates_created,
        SubFrames.gcal,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects_main, Columns.projects_side, Columns.domains,
            Columns.channels, Columns.readings,

            Columns.topics, Columns.writings,
        ]
    ),
    MyBlock.counts: Frame(
        SubFrames.dateval_created, SubFrames.dates, SubFrames.dates_created,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects,
            Columns.channels, Columns.readings,
            Columns.journals,
            Columns.writings,
        ]
    ),
    MyBlock.topics: Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects_main, Columns.projects_side, Columns.domains,
            Columns.channels, Columns.readings,
            Columns.writings, Columns.streams,

            Columns.journals, Columns.checks,
        ]
    ),
    MyBlock.streams: Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.people, Columns.locations,
            Columns.channels, Columns.readings,
            Columns.journals,
        ]
    ),
    MyBlock.readings: Frame(
        SubFrames.dateval_created, SubFrames.dates_begin, SubFrames.dates_created,
        [
            Columns.title_metadata,
            Columns.media_type,
            Columns.media_type_book,
            Columns.no_exp,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.channels,

            Columns.journals, Columns.streams,
            Columns.checks, Columns.writings,
        ]
    ),
    MyBlock.writings: Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.people, Columns.locations, Columns.channels,

            Columns.journals, Columns.checks,
            Columns.readings,
        ]
    ),

    MyBlock.weeks: Frame(
        [
            Columns.title_datetime,
            Columns.date_manual_range,

            Columns.itself,
        ]
    ),
    MyBlock.dates: Frame(
        [
            Columns.title_datetime, Columns.date_manual,
            Column(key=EmojiCode.CHECKER_FLAG + '동기화', alias='sync_status'),

            Columns.itself,
            Columns.weeks,
            Columns.journals,
            Columns.locations, Columns.channels,
        ]
    ),
    MyBlock.projects: Frame(
        SubFrames.dateval_created,
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


class FramesDepr:
    PERIODS = Frame(
        [
            Columns.title_datetime,
            Columns.date_manual_range,

            Columns.itself,
        ]
    )
    DATES = Frame(
        [
            Columns.title_datetime, Columns.date_manual,
            Column(key=EmojiCode.CHECKER_FLAG + '동기화', alias='sync_status'),

            Columns.itself,
            Columns.weeks,
            Columns.journals,
            Columns.locations, Columns.channels,
        ]
    )

    JOURNALS = Frame(
        SubFrames.dateval_created, SubFrames.dates, SubFrames.dates_created,
        SubFrames.gcal,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects_main, Columns.projects_side, Columns.domains,
            Columns.channels, Columns.readings,

            Columns.topics, Columns.writings,
        ]
    )
    CHECKS = Frame(
        SubFrames.dateval_created, SubFrames.dates, SubFrames.dates_created,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects,
            Columns.channels, Columns.readings,
            Columns.journals,
            Columns.writings,
        ]
    )
    TOPICS = Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects_main, Columns.projects_side, Columns.domains,
            Columns.channels, Columns.readings,
            Columns.writings, Columns.streams,

            Columns.journals, Columns.checks,
        ]
    )
    TASKS = Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.people, Columns.locations,
            Columns.channels, Columns.readings,
            Columns.journals,
        ]
    )
    READINGS = Frame(
        SubFrames.dateval_created, SubFrames.dates_begin, SubFrames.dates_created,
        [
            Columns.title_metadata,
            Columns.media_type,
            Columns.media_type_book,
            Columns.no_exp,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.channels,

            Columns.journals, Columns.streams,
            Columns.checks, Columns.writings,
        ]
    )
    WRITINGS = Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects, Columns.domains,
            Columns.people, Columns.locations, Columns.channels,

            Columns.journals, Columns.checks,
            Columns.readings,
        ]
    )

    PROJECTS = Frame(
        SubFrames.dateval_created,
        [

        ]
    )
    CHANNELS = Frame(
        [
            Columns.title_metadata,
            Columns.media_type,
            Columns.media_type_book,
        ]
    )
