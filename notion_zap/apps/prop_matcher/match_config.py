from notion_zap.apps.helpers.emoji_code import EmojiCode
from notion_zap.apps.myblock import MyBlock
from notion_zap.cli.core import \
    PropertyFrame as Frame, PropertyColumn as Column


class Columns:
    # basic properties
    title_generic = Column(key=EmojiCode.ORANGE_BOOK + '제목', alias='title')
    title_datetime = Column(key=EmojiCode.GREEN_BOOK + '제목', alias='title')
    title_metadata = Column(key=EmojiCode.BOOKSTACK + '제목', alias='title')

    media_type_from_below = Column(key=EmojiCode.RED_BOOK + '유형', alias='media_type')
    media_type_from_above = Column(key=EmojiCode.RED_BOOK + '읽기', alias='media_type')
    media_type_is_book = Column(alias='is_book', key='📔도서류', )
    get_dates_begin_from_created_time = Column(
        alias='get_dates_begin_from_created_time',
        key=EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')

    timestr = Column(key=EmojiCode.CALENDAR + '시간', alias='timestr', )
    manual_date = Column(key=EmojiCode.CALENDAR + '날짜', alias='manual_date', )
    manual_date_range = Column(key=EmojiCode.BIG_CALENDAR + '날짜 범위', alias='manual_date', )

    # relational properties
    itself = Column(key=EmojiCode.CYCLE + '재귀', alias='itself', )

    dates = Column(key=MyBlock.dates.prefix_title, alias='dates', )
    dates_created = Column(key=MyBlock.dates.prefix + '생성', alias='dates_created', )
    weeks = Column(key=MyBlock.weeks.prefix_title, alias='weeks', )

    notes = Column(key=MyBlock.notes.prefix_title, alias='notes', )

    processes = Column(key=MyBlock.processes.prefix_title, alias='processes', )
    journals = Column(key=MyBlock.journals.prefix_title, alias='journals', )

    tasks = Column(key=MyBlock.tasks.prefix_title, alias='tasks', )

    streams = Column(key=MyBlock.streams.prefix_title, alias='streams', )

    readings = Column(key=MyBlock.readings.prefix_title, alias='readings', )
    readings_begin = Column(key=MyBlock.readings.prefix + '시작', alias='readings_begin')

    summaries = Column(key=MyBlock.topics.prefix_title, alias='topics', )
    people = Column(key=MyBlock.people.prefix_title, alias='people', )
    locations = Column(key=MyBlock.locations.prefix_title, alias='locations', )
    writings = Column(key=MyBlock.writings.prefix_title, alias='writings', )
    channels = Column(key=MyBlock.channels.prefix_title, alias='channels', )


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
    dates_begin_readings = Frame([
        Column(key=MyBlock.weeks.prefix + '시작', aliases=['weeks_begin']),
        Column(key=MyBlock.dates.prefix + '시작', aliases=['dates_begin']),
    ])


Frames: dict[MyBlock, Frame] = {
    MyBlock.dates: Frame(
        [
            Columns.title_datetime, Columns.manual_date,

            Columns.weeks,
            Columns.journals,
        ]
    ),
    MyBlock.weeks: Frame(
        [
            Columns.title_datetime,
            Columns.manual_date_range,

            Columns.itself,
        ]
    ),

    MyBlock.processes: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.streams,
            Columns.readings, Columns.writings,
        ]
    ),

    MyBlock.journals: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        SubFrames.gcal,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.channels, Columns.readings,

            Columns.notes, Columns.writings,
        ]
    ),

    MyBlock.notes: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.processes, Columns.journals,
            Columns.tasks,
            Columns.readings, Columns.writings,
        ]
    ),
    MyBlock.issues: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.people, Columns.locations, Columns.channels,
            Columns.readings,
        ]
    ),
    MyBlock.tasks: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.people, Columns.locations, Columns.channels,
            Columns.readings,
        ]
    ),

    MyBlock.readings: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin_readings,
        [
            Columns.title_metadata,
            Columns.media_type_from_below,
            Columns.media_type_is_book,
            Columns.get_dates_begin_from_created_time,

            Columns.dates_created,
            Columns.streams,

            Columns.journals, Columns.tasks,
            Columns.processes, Columns.writings,

            Columns.channels,
        ]
    ),
    MyBlock.points: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.journals,
            Columns.readings, Columns.writings,
            Columns.streams, Columns.channels,
            Columns.summaries, Columns.people, Columns.locations,
        ]
    ),

    MyBlock.streams: Frame(
        SubFrames.date_auto_created,
        [
            Columns.media_type_from_above,
        ]
    ),

    # the followings are deprecated
    MyBlock.channels: Frame(
        [
            Columns.title_metadata,
            Columns.media_type_from_above,
            Columns.media_type_is_book,
        ]
    ),
    MyBlock.writings: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.readings, Columns.writings,
            Columns.streams, Columns.channels,
            Columns.summaries, Columns.people, Columns.locations,
        ]
    ),
    MyBlock.statuses: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.journals,
            Columns.tasks,
            Columns.readings, Columns.writings,
        ]
    ),
}
