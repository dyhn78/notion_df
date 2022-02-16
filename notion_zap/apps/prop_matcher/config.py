from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Cl


class EMOJI:
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

    # 가끔 뒤 공백이 짤리는 경우가 있다.
    # 인코딩 상태에서는 확인 불가능하니 아래 문자열을 그대로 붙여넣어야 한다.
    TIMER = '⏲️'

    BOOKSTACK = '📚'
    GREEN_BOOK = '📗'
    ORANGE_BOOK = '📙'


class PREFIX:
    PROJECTS = EMOJI.RED_CIRCLE
    TOPICS = EMOJI.RED_HEART
    CHANNELS = EMOJI.YELLOW_CIRCLE
    READINGS = EMOJI.YELLOW_HEART
    PEOPLE = EMOJI.ORANGE_CIRCLE
    LOCATIONS = EMOJI.ORANGE_HEART
    JOURNALS = EMOJI.PURPLE_CIRCLE
    TASKS = EMOJI.PURPLE_HEART
    CHECKS = EMOJI.BLUE_CIRCLE
    WRITINGS = EMOJI.BLUE_HEART


########################################################
###### basic properties ################################
########################################################
cl_generic_title = Cl(key=EMOJI.ORANGE_BOOK + '제목', tag='title')
cl_datetime_title = Cl(key=EMOJI.GREEN_BOOK + '제목', tag='title')
cl_media_title = Cl(key=EMOJI.BOOKSTACK + '제목', tag='title')

cl_no_exp = Cl(tag='no_exp', key='📓경험 없음', )

cl_media_type = Cl(key='📘유형', tag='media_type',
                   labels={'empty': '📌결정 전'})
cl_media_type_book = Cl(tag='is_book', key='📔도서류', )

cl_timestr = Cl(key='📆환경/시간', tag='timestr', )
cl_manual_date = Cl(key='📆날짜', tag='manual_date', )

fr_gcal = Frame([
    Cl(tag='gcal_sync_status', key='📔달력'),
    Cl(tag='gcal_link', key='📔링크'),
    Cl(tag='gcal_id', key='📔id'),
])

fr_dates_auto = Frame([
    Cl(key=EMOJI.TIMER + '날짜', tag='auto_datetime', ),
    Cl(key=EMOJI.TIMER + '날짜/D', tag='auto_date', ),
])
########################################################
###### relational properties ###########################
########################################################
cl_itself = Cl(key='🔁재귀', tag='itself', )

ic_periods = '🧶'
ic_dates = '🧵'
cl_periods = Cl(key=ic_periods + '기간', tag='periods', )
cl_dates = Cl(key=ic_dates + '날짜', tag='dates', )
fr_dates_actual = Frame([
    cl_periods,
    cl_dates
])
fr_dates_deadline = Frame([
    cl_periods_dl := Cl(key=ic_periods + '기한', tags=['periods_deadline', 'periods']),
    cl_dates_dl := Cl(key=ic_dates + '기한', tags=['dates_deadline', 'dates']),
])
fr_dates_begin = Frame([
    Cl(key=ic_periods + '시작', tags=['periods_begin', 'periods']),
    Cl(key=ic_dates + '시작', tags=['dates_begin', 'dates']),
])
fr_dates_created = Frame([
    Cl(key=ic_periods + '생성', tag='periods_created', ),
    Cl(key=ic_dates + '생성', tag='dates_created', )
])

cl_projects = Cl(key=PREFIX.PROJECTS + '실행', tag='projects', )
cl_projects_target = Cl(key=PREFIX.PROJECTS + '구성', tags=['projects_target', 'projects'])
cl_projects_perspective = Cl(key=PREFIX.PROJECTS + '관점', tag='projects_context', )
cl_projects_deadline = Cl(key=PREFIX.PROJECTS + '기한', tag='projects_deadline', )
cl_projects_total = Cl(key=PREFIX.PROJECTS + '종합', tag='projects_total', )

cl_topics = Cl(key=PREFIX.TOPICS + '꼭지', tag='topics', )
cl_topics_context = Cl(key=PREFIX.TOPICS + '맥락', tag='topics_context', )
cl_topics_total = Cl(key=PREFIX.TOPICS + '종합', tag='topics_total', )

cl_channels = Cl(key=PREFIX.CHANNELS + '채널', tag='channels', )
cl_channels_context = Cl(key=PREFIX.CHANNELS + '맥락', tag='channels_context', )
cl_channels_total = Cl(key=PREFIX.CHANNELS + '종합', tag='channels_total', )

cl_readings = Cl(key=PREFIX.READINGS + '읽기', tag='readings', )
cl_readings_context = Cl(key=PREFIX.READINGS + '맥락', tag='readings_context', )
cl_readings_begin = Cl(key=PREFIX.READINGS + '시작', tag='readings_begin')
cl_readings_deadline = Cl(key=PREFIX.READINGS + '기한', tag='readings_deadline', )
cl_readings_total = Cl(key=PREFIX.READINGS + '종합', tag='readings_total', )

cl_people = Cl(key=PREFIX.PEOPLE + '인물', tag='people', )

cl_locations = Cl(key=PREFIX.LOCATIONS + '🧡장소', tag='locations', )

cl_journals = Cl(key=PREFIX.JOURNALS + '일지', tag='checks', )
cl_journals_mentioned = Cl(key=PREFIX.JOURNALS + '언급', tag='journals_induced', )

cl_tasks = Cl(key=PREFIX.TASKS + '요점', tag='tasks', )

cl_checks = Cl(key=PREFIX.CHECKS + '진도', tag='journals', )

cl_writings = Cl(key=PREFIX.WRITINGS + '쓰기', tag='writings', )
cl_writings_mentioned = Cl(key=PREFIX.WRITINGS + '언급', tag='writings_induced', )


class MatchFrames:
    PERIODS = Frame(
        [
            cl_datetime_title,
            Cl(key='📅날짜 범위', tag='manual_date_range'),

            cl_itself,
        ]
    )
    DATES = Frame(
        [
            cl_datetime_title, cl_manual_date,
            Cl(key='🏁동기화', tag='sync_status'),

            cl_itself,
            cl_periods,
            cl_journals,
            cl_locations, cl_channels,
        ]
    )

    JOURNALS = Frame(
        fr_dates_auto, fr_dates_actual, fr_dates_created,
        fr_gcal,
        [
            cl_generic_title,
            cl_timestr,

            cl_itself,
            cl_projects, cl_projects_perspective, cl_topics,
            cl_channels, cl_readings,

            cl_tasks,
            cl_checks,
        ]
    )
    TASKS = Frame(
        fr_dates_auto, fr_dates_actual,
        [
            cl_generic_title,
            cl_timestr,

            cl_itself,
            cl_projects, cl_topics,
            cl_people, cl_locations,
            cl_channels, cl_readings,
            cl_journals,
        ]
    )
    CHECKS = Frame(
        fr_dates_auto, fr_dates_actual, fr_dates_created,
        [
            cl_generic_title,
            cl_timestr,

            cl_itself,
            cl_projects,
            cl_readings, cl_channels,
            cl_journals,
            cl_writings,
        ]
    )
    WRITINGS = Frame(
        fr_dates_auto, fr_dates_actual,
        [
            cl_generic_title,
            cl_timestr,

            cl_itself,
            cl_projects_target, cl_projects_perspective, cl_topics,
            cl_people, cl_locations,
            cl_channels, cl_readings,
            cl_journals,

            cl_checks,
        ]
    )

    CHANNELS = Frame(
        [
            cl_media_title,
            cl_media_type,
            cl_media_type_book,
        ]
    )
    READINGS = Frame(
        fr_dates_auto, fr_dates_begin, fr_dates_created,
        [
            cl_media_title,
            cl_media_type,
            cl_media_type_book,
            cl_no_exp,

            cl_itself,
            cl_projects, cl_topics,
            cl_channels,

            cl_journals, cl_tasks,
            cl_checks, cl_writings,
        ]
    )
