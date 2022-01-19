from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Cl

"""
날짜 관련된 formula 속성의 값은
그리니치 시간대를 기준으로 그때그때 계산하는 것 같다.
노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서
이쪽 파이썬 코드에서 처리하는 식으로 움직이자.
"""

########################################################
###### basic properties ################################
########################################################
cl_title = Cl(key='📚제목', tag='title')

cl_timestr = Cl(key='📆환경/시간', tag='timestr', )
cl_manual_date = Cl(key='📆날짜', tag='manual_date', )
cl_media_type = Cl(key='📘유형', tag='media_type',
                   labels={'empty': '📌결정 전'})
fr_gcal = Frame([
    Cl(tag='gcal_sync_status', key='📔달력'),
    Cl(tag='gcal_link', key='📔링크'),
    Cl(tag='gcal_id', key='📔id'),
])
ic_dates_auto = '⏲️'
fr_dates_auto = Frame([
    Cl(key='날짜값' + ic_dates_auto, tag='auto_date', ),
    Cl(key='날짜' + ic_dates_auto, tag='auto_datetime', )
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

ic_projects = '🔴'
cl_projects = Cl(key=ic_projects + '실행', tag='projects', )
cl_projects_target = Cl(key=ic_projects + '구성', tags=['projects_target', 'projects'])
cl_projects_context = Cl(key=ic_projects + '맥락', tag='projects_context', )
cl_projects_deadline = Cl(key=ic_projects + '기한', tag='projects_deadline', )
cl_projects_total = Cl(key=ic_projects + '종합', tag='projects_total', )

ic_topics = '❤'
cl_topics = Cl(key=ic_topics + '꼭지', tag='topics', )
cl_topics_context = Cl(key=ic_topics + '맥락', tag='topics_context', )
cl_topics_total = Cl(key=ic_topics + '종합', tag='topics_total', )

ic_channels = '🟡'
cl_channels = Cl(key=ic_channels + '채널', tag='channels', )
cl_channels_context = Cl(key=ic_channels + '맥락', tag='channels_context', )
cl_channels_total = Cl(key=ic_channels + '종합', tag='channels_total', )

ic_readings = '💛'
cl_readings = Cl(key=ic_readings + '읽기', tag='readings', )
cl_readings_context = Cl(key=ic_readings + '맥락', tag='readings_context', )
cl_readings_begin = Cl(key=ic_readings + '시작', tag='readings_begin')
cl_readings_deadline = Cl(key=ic_readings + '기한', tag='readings_deadline', )
cl_readings_total = Cl(key=ic_readings + '종합', tag='readings_total', )

cl_people = Cl(key='🟠인물', tag='people', )

cl_locations = Cl(key='🧡장소', tag='locations', )

ic_journals = '🟣'
cl_journals = Cl(key=ic_journals + '일지', tag='journals', )
cl_journals_context = Cl(key=ic_journals + '맥락', tag='journals_context', )
cl_journals_induced = Cl(key=ic_journals + '언급', tag='journals_induced', )

ic_writings = '💜'
cl_writings = Cl(key=ic_writings + '쓰기', tag='writings', )
cl_writings_induced = Cl(key=ic_writings + '언급', tag='writings_induced', )

ic_schedules = '🔵'
cl_schedules = Cl(key=ic_schedules + '계획', tag='schedules', )
cl_schedules_deadline = Cl(key=ic_schedules + '기한', tag='schedules_deadline', )

ic_tasks = '💙'
cl_tasks = Cl(key=ic_tasks + '요점', tag='tasks', )


class MatchFrames:
    PERIODS = Frame(
        [
            cl_title, cl_itself,
            Cl(key='📅날짜 범위', tag='manual_date_range')
        ]
    )
    DATES = Frame(
        [
            cl_title, cl_itself, cl_manual_date,
            cl_periods,
            cl_journals,
            cl_locations, cl_channels,
            Cl(key='🏁동기화', tag='sync_status'),
        ]
    )

    CHANNELS = Frame(
        [
            cl_title,
            cl_media_type,
        ]
    )
    READINGS = Frame(
        fr_dates_auto, fr_dates_begin, fr_dates_created,
        [
            cl_title, cl_itself,
            cl_media_type,
            Cl(tag='no_exp', key='🏁경험 없음<-진행', ),
            Cl(tag='is_book', key='📘도서<-유형', ),

            cl_journals,
            cl_schedules,

            cl_projects,
            cl_channels,
        ]
    )

    JOURNALS = Frame(
        fr_dates_auto, fr_gcal, fr_dates_actual, fr_dates_created,
        [
            cl_title, cl_itself, cl_timestr,

            cl_writings_induced,
            cl_schedules, cl_tasks,

            cl_projects, cl_projects_context,
            cl_readings, cl_readings_context,
            cl_channels, cl_channels_context,
            cl_topics_context,
        ]
    )
    WRITINGS = Frame(
        fr_dates_auto, fr_dates_actual,
        [
            cl_title, cl_itself, cl_timestr,

            cl_journals_context,
            cl_schedules,

            cl_projects_target,
            cl_topics,
            cl_channels,
            cl_readings,
        ]
    )
    SCHEDULES = Frame(
        fr_dates_auto, fr_gcal, fr_dates_deadline, fr_dates_created,
        [
            cl_title, cl_itself, cl_timestr,

            cl_journals, cl_tasks,

            cl_projects,
            cl_topics,
            cl_channels,
            cl_readings,
        ]
    )
    TASKS = Frame(
        fr_dates_auto, fr_dates_actual,
        [
            cl_title, cl_itself,

            cl_journals, cl_schedules,

            cl_topics,
            cl_channels,
            cl_readings,
        ]
    )
