from notion_zap.cli.structs import \
    PropertyFrame as Frame, PropertyColumn as Cl

"""
날짜 관련된 formula 속성의 값은
그리니치 시간대를 기준으로 그때그때 계산하는 것 같다.
노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서 이쪽 파이썬 코드에서
처리하는 식으로 움직이자.
"""

Cl_title = Cl(tag='title', key='📚제목')

Cl_to_itself = Cl(tag='to_itself', key='🔁재귀')
Cl_to_periods = Cl(tag='to_periods', key='🧶기간')
Cl_to_dates = Cl(tag='to_dates', key='🧵날짜')
Cl_to_journals = Cl(tag='to_journals', key='🎵일과')
Cl_to_writings = Cl(tag='to_writings', key='🎵일지')
Cl_to_schedules = Cl(tag='to_schedules', key='📘안배')

Cl_to_themes = Cl(tag='to_themes', key='📕수행')
Cl_to_locations = Cl(tag='to_locations', key='📙장소')
Cl_to_channels = Cl(tag='to_channels', key='📒채널')
Cl_to_readings = Cl(tag='to_readings', key='📒읽기')

Cl_auto_date = Cl(tag='auto_date', key='날짜값⏲️')
Cl_auto_time = Cl(tag='auto_datetime', key='날짜⏲️')
Fr_AUTO_DATE = Frame([Cl_auto_date, Cl_auto_time])

Cl_timestr = Cl(tag='timestr', key='📆환경/시간')
Cl_manual_date = Cl(tag='manual_date', key='📆날짜')

Cl_media_type = Cl(tag='media_type', key='🔵유형', labels={'empty': '🛠️결정 전'})


class MatchFrames:
    PERIODS = Frame(
        [
            Cl_title, Cl_to_itself,
            Cl(tag='manual_date_range', key='📅날짜 범위')
        ]
    )
    # PERIODS.add_alias('title', 'index_as_target')
    # PERIODS.add_alias('manual_date_range', 'index_as_domain')

    DATES = Frame(
        [
            Cl_title, Cl_to_itself, Cl_manual_date,
            Cl_to_periods,
            Cl_to_journals,
            Cl_to_locations, Cl_to_channels,
            Cl(tag='sync_status', key='🏁동기화'),
        ]
    )
    # DATES.add_alias('title', 'index_as_target')
    # DATES.add_alias('manual_date', 'index_as_domain')

    JOURNALS = Frame(
        Fr_AUTO_DATE,
        [
            Cl_title, Cl_to_itself, Cl_timestr,
            Cl_to_periods, Cl_to_dates,
            Cl(tag='up_self', key='🎵구성'),
            Cl(tag='down_self', key='🎵요소'),

            Cl_to_themes, Cl_to_locations, Cl_to_readings, Cl_to_channels,
        ]
    )
    SCHEDULES = Frame(
        Fr_AUTO_DATE,
        [
            Cl_title, Cl_to_itself, Cl_timestr,
            Cl(tag='to_scheduled_periods', key='🧶기간'),
            Cl(tag='to_scheduled_dates', key='🧵날짜'),
            Cl(tag='to_created_periods', key='🧶생성'),
            Cl(tag='to_created_dates', key='🧵생성'),

            Cl_to_themes, Cl_to_channels, Cl_to_readings,

            Cl(tag='gcal_sync_status', key='🏁동기화'),
            Cl(tag='gcal_link', key='📚Gcal'),
            Cl(tag='gcal_id', key='📚Gcal_id'),
        ]
    )
    WRITINGS = Frame(
        Fr_AUTO_DATE,
        [
            Cl_title, Cl_to_itself, Cl_timestr,
            Cl_to_periods, Cl_to_dates, Cl_to_journals, Cl_to_schedules,

            Cl_to_channels, Cl_to_readings,
            Cl(tag='to_themes', key='📕맥락'),
        ]
    )
    MEMOS = Frame(
        Fr_AUTO_DATE,
        [
            Cl_title, Cl_to_itself,
            Cl_to_periods, Cl_to_dates, Cl_to_journals,
        ]
    )

    READINGS = Frame(
        Fr_AUTO_DATE,
        [
            Cl_title, Cl_to_itself,
            Cl(tag='to_periods', key='🧶시작'),
            Cl(tag='to_dates', key='🧵시작'),
            Cl_to_journals, Cl_to_schedules,
            Cl_to_themes, Cl_to_channels,

            Cl_media_type,
            Cl(tag='no_exp', key='🏁경험 없음<-경과'),
            Cl(tag='is_book', key='🔵도서<-유형'),
        ]
    )

    CHANNELS = Frame(
        [
            Cl_title,
            Cl_media_type,
        ]
    )
