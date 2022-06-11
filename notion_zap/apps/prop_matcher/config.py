from notion_zap.apps.config import MyBlock
from notion_zap.apps.emoji_code import EmojiCode
from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Column


class Columns:
    # basic properties
    title_generic = Column(key=EmojiCode.ORANGE_BOOK + '제목', alias='title')
    title_datetime = Column(key=EmojiCode.GREEN_BOOK + '제목', alias='title')
    title_metadata = Column(key=EmojiCode.BOOKSTACK + '제목', alias='title')

    media_type_from_below = Column(key=EmojiCode.BLUE_BOOK + '유형', alias='media_type')
    media_type_from_above = Column(key=EmojiCode.BLUE_BOOK + '읽기', alias='media_type')
    media_type_is_book = Column(alias='is_book', key='📔도서류', )
    get_dates_begin_from_created_time = Column(
        alias='get_dates_begin_from_created_time',
        key=EmojiCode.BLACK_NOTEBOOK + '시작일<-생성시간')

    timestr = Column(key=EmojiCode.CALENDAR + '시간', alias='timestr', )
    manual_date = Column(key=EmojiCode.CALENDAR + '날짜', alias='manual_date', )
    manual_date_range = Column(key=EmojiCode.BIG_CALENDAR + '날짜 범위', alias='manual_date', )

    # relational properties
    itself = Column(key=EmojiCode.CYCLE + '재귀', alias='itself', )

    weeks = Column(key=MyBlock.weeks.prefix_title, alias='weeks', )
    dates = Column(key=MyBlock.dates.prefix_title, alias='dates', )
    dates_created = Column(key=MyBlock.dates.prefix + '생성', alias='dates_created', )

    journals = Column(key=MyBlock.journals.prefix_title, alias='journals', )
    events = Column(key=MyBlock.events.prefix_title, alias='events', )
    notes = Column(key=MyBlock.notes.prefix_title, alias='notes', )

    issues = Column(key=MyBlock.issues.prefix_title, alias='issues', )
    targets = Column(key=MyBlock.targets.prefix_title, alias='targets', )

    streams = Column(key=MyBlock.streams.prefix_title, alias='streams', )
    channels = Column(key=MyBlock.channels.prefix_title, alias='channels', )

    readings = Column(key=MyBlock.readings.prefix_title, alias='readings', )
    readings_begin = Column(key=MyBlock.readings.prefix + '시작', alias='readings_begin')

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
            Columns.events,
            Columns.locations, Columns.channels,
        ]
    ),

    MyBlock.journals: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.itself,
            Columns.streams,
            Columns.readings, Columns.notes,
        ]
    ),
    MyBlock.events: Frame(
        SubFrames.date_auto_created, SubFrames.dates,
        SubFrames.gcal,
        [
            Columns.title_generic,
            Columns.timestr,
            Columns.dates_created,

            Columns.itself,
            Columns.channels, Columns.readings,

            Columns.targets, Columns.notes,
        ]
    ),
    MyBlock.notes: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.readings, Columns.notes,
            Columns.streams, Columns.channels,
            Columns.domains, Columns.people, Columns.locations,
        ]
    ),

    MyBlock.issues: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.itself,
            Columns.people, Columns.locations, Columns.channels,
            Columns.readings,
        ]
    ),
    MyBlock.targets: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.events, Columns.journals,
            Columns.issues,
            Columns.channels,
            Columns.readings, Columns.notes,
        ]
    ),

    MyBlock.readings: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_metadata,
            Columns.media_type_from_below,
            Columns.media_type_is_book,
            Columns.get_dates_begin_from_created_time,

            Columns.dates_created,
            Columns.itself,
            Columns.streams, Columns.channels,

            Columns.events, Columns.issues,
            Columns.journals, Columns.notes,
        ]
    ),
    MyBlock.points: Frame(
        SubFrames.date_auto_created, SubFrames.dates_begin,
        [
            Columns.title_generic,

            Columns.itself,
            Columns.events,
            Columns.readings, Columns.notes,
            Columns.streams, Columns.channels,
            Columns.domains, Columns.people, Columns.locations,
        ]
    ),

    MyBlock.streams: Frame(
        SubFrames.date_auto_created,
        [
            Columns.media_type_from_above,
        ]
    ),
    MyBlock.channels: Frame(
        [
            Columns.title_metadata,
            Columns.media_type_from_above,
            Columns.media_type_is_book,
        ]
    )
}
