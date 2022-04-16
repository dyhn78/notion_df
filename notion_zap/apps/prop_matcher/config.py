from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Cl, PropertyMarkedValue as Label


class EMOJI:
    RED_CIRCLE = '🔴'
    RED_HEART = '❤'
    ORANGE_HEART = '🟠'
    ORANGE_CIRCLE = '🧡'
    ORANGE_DIAMOND = '🔶'
    YELLOW_CIRCLE = '🟡'
    YELLOW_HEART = '💛'
    PURPLE_CIRCLE = '🟣'
    PURPLE_HEART = '💜'
    BLUE_CIRCLE = '🔵'
    BLUE_HEART = '💙'
    BROWN_CIRCLE = '🟤'
    BROWN_HEART = '🤎'

    BOOKSTACK = '📚'
    GREEN_BOOK = '📗'
    ORANGE_BOOK = '📙'
    BLUE_BOOK = '📘'
    BROWN_NOTEBOOK = '📔'
    YELLOW_NOTEBOOK = '📒'
    BLACK_NOTEBOOK = '📓'

    CYCLE = '🔁'
    CHECKER_FLAG = '🏁'
    YARN = '🧶'
    THREAD = '🧵'
    CALENDAR = '📆'
    BIG_CALENDAR = '📅'
    TIMER = '⏲️'  # 가끔 Notion 환경에 뒤 공백이 짤려 삽입된 경우가 있다.
    GLOBE_ASIA = '🌏'


class PREFIX:
    SYSTEMS = EMOJI.GLOBE_ASIA

    JOURNALS = EMOJI.PURPLE_CIRCLE
    CHECKS = EMOJI.PURPLE_HEART
    TOPICS = EMOJI.BLUE_CIRCLE
    TASKS = EMOJI.BLUE_HEART
    READINGS = EMOJI.YELLOW_CIRCLE
    WRITINGS = EMOJI.YELLOW_HEART

    PERIODS = EMOJI.BROWN_CIRCLE
    DATES = EMOJI.BROWN_HEART
    PROJECTS = EMOJI.RED_CIRCLE
    DOMAINS = EMOJI.RED_HEART
    CHANNELS = EMOJI.ORANGE_CIRCLE
    PEOPLE = EMOJI.ORANGE_HEART
    LOCATIONS = EMOJI.ORANGE_DIAMOND



class Columns:
    # basic properties
    title_generic = Cl(key=EMOJI.ORANGE_BOOK + '제목', alias='title')
    title_datetime = Cl(key=EMOJI.GREEN_BOOK + '제목', alias='title')
    title_metadata = Cl(key=EMOJI.BOOKSTACK + '제목', alias='title')

    no_exp = Cl(key=EMOJI.BLACK_NOTEBOOK + '경험 없음', alias='no_exp', )

    media_type = Cl(key=EMOJI.BLUE_BOOK + '유형', alias='media_type',
                    marked_values=[Label('📌결정 전', 'empty')])
    media_type_book = Cl(alias='is_book', key='📔도서류', )

    timestr = Cl(key=EMOJI.CALENDAR + '시간', alias='timestr', )
    dateval_manual = Cl(key=EMOJI.CALENDAR + '날짜', alias='dateval_manual', )
    dateval_manual_range = Cl(key=EMOJI.BIG_CALENDAR + '날짜 범위',
                              alias='manual_date_range', )

    # relational properties
    itself = Cl(key=EMOJI.CYCLE + '재귀', alias='itself', )

    periods = Cl(key=PREFIX.PERIODS + '주간', alias='periods', )
    dates = Cl(key=PREFIX.DATES + '일간', alias='dates', )

    journals = Cl(key=PREFIX.JOURNALS + '일지', alias='journals', )
    checks = Cl(key=PREFIX.CHECKS + '진도', alias='checks', )

    topics = Cl(key=PREFIX.TOPICS + '발전', alias='topics', )
    tasks = Cl(key=PREFIX.TASKS + '요점', alias='tasks', )

    readings = Cl(key=PREFIX.READINGS + '읽기', alias='readings', )
    readings_begin = Cl(key=PREFIX.READINGS + '시작', alias='readings_begin')
    writings = Cl(key=PREFIX.WRITINGS + '쓰기', alias='writings', )

    projects = Cl(key=PREFIX.PROJECTS + '실행', alias='projects', )
    projects_main = Cl(key=PREFIX.PROJECTS + '중심', aliases=['projects_main', 'projects'])
    projects_side = Cl(key=PREFIX.PROJECTS + '주변', alias='projects_side')
    domains = Cl(key=PREFIX.DOMAINS + '꼭지', alias='domains', )

    channels = Cl(key=PREFIX.CHANNELS + '채널', alias='channels', )
    people = Cl(key=PREFIX.PEOPLE + '인물', alias='people', )
    locations = Cl(key=PREFIX.LOCATIONS + '장소', alias='locations', )


class SubFrames:
    gcal = Frame([
        Cl(alias='gcal_sync_status', key='📔달력'),
        Cl(alias='gcal_link', key=EMOJI.YELLOW_NOTEBOOK + '링크'),
        Cl(alias='gcal_id', key=EMOJI.YELLOW_NOTEBOOK + 'id'),
    ])

    dateval_created = Frame([
        Cl(key=EMOJI.TIMER + '일시', alias='auto_datetime', ),
        Cl(key=EMOJI.TIMER + '날짜', alias='auto_date', ),
    ])

    dates = Frame([
        Columns.periods,
        Columns.dates
    ])
    dates_deadline = Frame([
        Cl(key=PREFIX.PERIODS + '기한', aliases=['periods_deadline', 'periods']),
        Cl(key=PREFIX.DATES + '기한', aliases=['dates_deadline', 'dates']),
    ])
    dates_begin = Frame([
        Cl(key=PREFIX.PERIODS + '시작', aliases=['periods_begin', 'periods']),
        Cl(key=PREFIX.DATES + '시작', aliases=['dates_begin', 'dates']),
    ])
    dates_created = Frame([
        Cl(key=PREFIX.PERIODS + '생성', alias='periods_created', ),
        Cl(key=PREFIX.DATES + '생성', alias='dates_created', )
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
            Cl(key=EMOJI.CHECKER_FLAG + '동기화', alias='sync_status'),

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
