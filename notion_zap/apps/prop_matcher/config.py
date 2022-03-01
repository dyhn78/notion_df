from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Cl


class EMOJI:
    CYCLE = '🔁'
    CHECKER_FLAG = '🏁'

    YARN = '🧶'
    THREAD = '🧵'
    CALENDAR = '📆'
    BIG_CALENDAR = '📅'
    TIMER = '⏲️'  # 가끔 Notion 환경에 뒤 공백이 짤려 삽입된 경우가 있다.

    RED_CIRCLE = '🔴'
    RED_HEART = '❤'
    ORANGE_HEART = '🟠'
    ORANGE_CIRCLE = '🧡'
    YELLOW_CIRCLE = '🟡'
    YELLOW_HEART = '💛'
    PURPLE_CIRCLE = '🟣'
    PURPLE_HEART = '💜'
    BLUE_CIRCLE = '🔵'
    BLUE_HEART = '💙'

    BOOKSTACK = '📚'
    GREEN_BOOK = '📗'
    ORANGE_BOOK = '📙'
    BLUE_BOOK = '📘'
    BROWN_NOTEBOOK = '📔'
    YELLOW_NOTEBOOK = '📒'
    BLACK_NOTEBOOK = '📓'


class PREFIX:
    PERIODS = EMOJI.YARN
    DATES = EMOJI.THREAD
    JOURNALS = EMOJI.PURPLE_CIRCLE
    CHECKS = EMOJI.PURPLE_HEART
    TOPICS = EMOJI.BLUE_CIRCLE
    TASKS = EMOJI.BLUE_HEART
    WRITINGS = EMOJI.BLUE_HEART

    PROJECTS = EMOJI.RED_CIRCLE
    DOMAINS = EMOJI.RED_HEART
    CHANNELS = EMOJI.YELLOW_CIRCLE
    READINGS = EMOJI.YELLOW_HEART
    PEOPLE = EMOJI.ORANGE_CIRCLE
    LOCATIONS = EMOJI.ORANGE_HEART


# basic properties

class Columns:
    title_generic = Cl(key=EMOJI.ORANGE_BOOK + '제목', tag='title')
    title_datetime = Cl(key=EMOJI.GREEN_BOOK + '제목', tag='title')
    title_metadata = Cl(key=EMOJI.BOOKSTACK + '제목', tag='title')

    no_exp = Cl(tag='no_exp', key=EMOJI.BLACK_NOTEBOOK + '경험 없음', )

    media_type = Cl(key=EMOJI.BLUE_BOOK + '유형', tag='media_type',
                    labels={'empty': '📌결정 전'})
    media_type_book = Cl(tag='is_book', key='📔도서류', )

    timestr = Cl(key=EMOJI.CALENDAR + '시간', tag='timestr', )
    dateval_manual = Cl(key=EMOJI.CALENDAR + '날짜', tag='dateval_manual', )
    dateval_manual_range = Cl(key=EMOJI.BIG_CALENDAR + '날짜 범위',
                              tag='manual_date_range', )

    # relational properties
    itself = Cl(key=EMOJI.CYCLE + '재귀', tag='itself', )

    periods = Cl(key=EMOJI.YARN + '기간', tag='periods', )
    dates = Cl(key=EMOJI.THREAD + '날짜', tag='dates', )

    journals = Cl(key=PREFIX.JOURNALS + '일지', tag='journals', )
    journals_mentioned = Cl(key=PREFIX.JOURNALS + '언급', tag='journals_induced', )
    checks = Cl(key=PREFIX.CHECKS + '진도', tag='checks', )

    topics = Cl(key=PREFIX.TOPICS + '전개', tag='topics', )
    tasks = Cl(key=PREFIX.TASKS + '요점', tag='tasks', )
    writings = Cl(key=PREFIX.WRITINGS + '쓰기', tag='writings', )
    writings_mentioned = Cl(key=PREFIX.WRITINGS + '언급', tag='writings_induced', )

    projects = Cl(key=PREFIX.PROJECTS + '실행', tag='projects', )
    projects_main = Cl(key=PREFIX.PROJECTS + '중심', tags=['projects_main', 'projects'])
    projects_side = Cl(key=PREFIX.PROJECTS + '주변', tag='projects_side')

    # deprecated?
    projects_target = Cl(key=PREFIX.PROJECTS + '구성', tags=['projects_target', 'projects'])
    projects_perspective = Cl(key=PREFIX.PROJECTS + '관점', tag='projects_context', )
    projects_deadline = Cl(key=PREFIX.PROJECTS + '기한', tag='projects_deadline', )
    projects_total = Cl(key=PREFIX.PROJECTS + '종합', tag='projects_total', )
    #

    domains = Cl(key=PREFIX.DOMAINS + '꼭지', tag='domains', )
    domains_context = Cl(key=PREFIX.DOMAINS + '맥락', tag='domains_context', )
    domains_total = Cl(key=PREFIX.DOMAINS + '종합', tag='domains_total', )

    channels = Cl(key=PREFIX.CHANNELS + '채널', tag='channels', )
    channels_context = Cl(key=PREFIX.CHANNELS + '맥락', tag='channels_context', )
    channels_total = Cl(key=PREFIX.CHANNELS + '종합', tag='channels_total', )

    readings = Cl(key=PREFIX.READINGS + '읽기', tag='readings', )
    readings_context = Cl(key=PREFIX.READINGS + '맥락', tag='readings_context', )
    readings_begin = Cl(key=PREFIX.READINGS + '시작', tag='readings_begin')
    readings_deadline = Cl(key=PREFIX.READINGS + '기한', tag='readings_deadline', )
    readings_total = Cl(key=PREFIX.READINGS + '종합', tag='readings_total', )

    people = Cl(key=PREFIX.PEOPLE + '인물', tag='people', )

    locations = Cl(key=PREFIX.LOCATIONS + '장소', tag='locations', )


class SubFrames:
    gcal = Frame([
        Cl(tag='gcal_sync_status', key='📔달력'),
        Cl(tag='gcal_link', key=EMOJI.YELLOW_NOTEBOOK + '링크'),
        Cl(tag='gcal_id', key=EMOJI.YELLOW_NOTEBOOK + 'id'),
    ])

    dateval_created = Frame([
        Cl(key=EMOJI.TIMER + '날짜', tag='auto_datetime', ),
        Cl(key=EMOJI.TIMER + '날짜/D', tag='auto_date', ),
    ])

    dates = Frame([
        Columns.periods,
        Columns.dates
    ])
    dates_deadline = Frame([
        Cl(key=EMOJI.YARN + '기한', tags=['periods_deadline', 'periods']),
        Cl(key=EMOJI.THREAD + '기한', tags=['dates_deadline', 'dates']),
    ])
    dates_begin = Frame([
        Cl(key=EMOJI.YARN + '시작', tags=['periods_begin', 'periods']),
        Cl(key=EMOJI.THREAD + '시작', tags=['dates_begin', 'dates']),
    ])
    dates_created = Frame([
        Cl(key=EMOJI.YARN + '생성', tag='periods_created', ),
        Cl(key=EMOJI.THREAD + '생성', tag='dates_created', )
    ])


class Frames:
    PERIODS = Frame(
        [
            Columns.title_datetime,
            Columns.dateval_manual_range,

            Columns.itself,
        ]
    )
    DATES = Frame(
        [
            Columns.title_datetime, Columns.dateval_manual,
            Cl(key=EMOJI.CHECKER_FLAG + '동기화', tag='sync_status'),

            Columns.itself,
            Columns.periods,
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
            Columns.readings, Columns.channels,
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
            Columns.projects, Columns.domains,
            Columns.channels, Columns.readings,
            Columns.writings, Columns.tasks,

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
    WRITINGS = Frame(
        SubFrames.dateval_created, SubFrames.dates,
        [
            Columns.title_generic,
            Columns.timestr,

            Columns.itself,
            Columns.projects_target, Columns.projects_perspective, Columns.domains,
            Columns.people, Columns.locations,
            Columns.channels, Columns.readings,
            Columns.journals,

            Columns.checks,
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

            Columns.journals, Columns.tasks,
            Columns.checks, Columns.writings,
        ]
    )
