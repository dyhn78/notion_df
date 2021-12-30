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
                   labels={'empty': '🛠️결정 전'})
fr_gcal = Frame([
    Cl(tag='gcal_sync_status', key='📔달력'),
    Cl(tag='gcal_link', key='📔링크'),
    Cl(tag='gcal_id', key='📔id'),
])
fr_auto_date = Frame([
    Cl(key='날짜값⏲️', tag='auto_date', ),
    Cl(key='날짜⏲️', tag='auto_datetime', )
])
########################################################
###### relational properties ###########################
########################################################
cl_to_itself = Cl(key='🔁재귀', tag='to_itself', )
cl_to_periods = Cl(key='🧶기간', tag='to_periods', )
cl_to_dates = Cl(key='🧵날짜', tag='to_dates', )
fr_dual_dates = Frame([
    cl_to_periods,
    cl_to_dates,
    Cl(key='🧶생성', tag='to_created_periods', ),
    Cl(key='🧵생성', tag='to_created_dates', ),
])

cl_to_journals = Cl(key='🟣일지', tag='to_journals', )
cl_to_writings = Cl(key='💜쓰기', tag='to_writings', )
cl_to_tasks = Cl(key='🔵과제', tag='to_tasks', )
cl_to_schedules = Cl(key='💙안배', tag='to_schedules', )

cl_to_projects = Cl(key='🔴실행', tag='to_projects', )
cl_to_ideas = Cl(key='❤관점', tag='to_ideas', )
cl_to_people = Cl(key='🟠인물', tag='to_people', )
cl_to_locations = Cl(key='🧡장소', tag='to_locations', )
cl_to_channels = Cl(key='🟡채널', tag='to_channels', )
cl_to_readings = Cl(key='💛읽기', tag='to_readings', )


class MatchFrames:
    PERIODS = Frame(
        [
            cl_title, cl_to_itself,
            Cl(key='📅날짜 범위', tag='manual_date_range')
        ]
    )
    DATES = Frame(
        [
            cl_title, cl_to_itself, cl_manual_date,
            cl_to_periods,
            cl_to_journals,
            cl_to_locations, cl_to_channels,
            Cl(key='🏁동기화', tag='sync_status'),
        ]
    )

    JOURNALS = Frame(
        fr_auto_date, fr_gcal, fr_dual_dates,
        [
            cl_title, cl_to_itself, cl_timestr,

            cl_to_projects, cl_to_locations, cl_to_readings, cl_to_channels,
        ]
    )
    WRITINGS = Frame(
        fr_auto_date,
        [
            cl_title, cl_to_itself, cl_timestr,
            cl_to_periods, cl_to_dates, cl_to_journals, cl_to_schedules,

            cl_to_channels, cl_to_readings,
            cl_to_projects.key_change('🔴구성'),
            cl_to_ideas
        ]
    )
    TASKS = Frame(
        fr_auto_date,
        [
            cl_title, cl_to_itself,
            cl_to_periods, cl_to_dates, cl_to_journals,
        ]
    )
    SCHEDULES = Frame(
        fr_auto_date, fr_gcal, fr_dual_dates,
        [
            cl_title, cl_to_itself, cl_timestr,

            cl_to_projects, cl_to_channels, cl_to_readings,

        ]
    )

    READINGS = Frame(
        fr_auto_date,
        [
            cl_title, cl_to_itself,
            cl_to_periods.key_change('🧶시작'),
            cl_to_dates.key_change('🧵시작'),
            cl_to_journals, cl_to_schedules,
            cl_to_projects, cl_to_channels,

            cl_media_type,
            Cl(tag='no_exp', key='🏁경험 없음<-경과', ),
            Cl(tag='is_book', key='🔵도서<-유형', ),
        ]
    )
    CHANNELS = Frame(
        [
            cl_title,
            cl_media_type.key_change('📘읽기'),
        ]
    )
