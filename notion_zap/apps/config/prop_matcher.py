from notion_zap.cli.struct import \
    PropertyFrame as Frame, PropertyColumn as Cl

"""
날짜 관련된 formula 속성의 값은
그리니치 시간대를 기준으로 그때그때 계산하는 것 같다.
노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서 이쪽 파이썬 코드에서
처리하는 식으로 움직이자.
"""

_title = Cl(tag='title', key='📚제목')

_to_itself = Cl(tag='to_itself', key='🔁재귀')
_to_periods = Cl(tag='to_periods', key='🧶기간')
_to_dates = Cl(tag='to_dates', key='🧶날짜')
_to_journals = Cl(tag='to_journals', key='🧵일지')

_to_themes = Cl(tag='to_themes', key='📕수행')
_to_locations = Cl(tag='to_locations', key='📙장소')
_to_channels = Cl(tag='to_channels', key='📒채널')
_to_readings = Cl(tag='to_readings', key='📒읽기')

_auto_date = Cl(tag='auto_date', key='날짜값⏲️')
_auto_time = Cl(tag='auto_datetime', key='날짜⏲️')
_AUTO_DATE = Frame([_auto_date, _auto_time])

_timestr = Cl(tag='timestr', key='📆환경/시간')
_manual_date = Cl(tag='manual_date', key='📆날짜')


class MatchFrames:
    PERIODS = Frame(
        [
            _title, _to_itself,
            Cl(tag='manual_date_range', key='📅날짜 범위')
        ]
    )
    # PERIODS.add_alias('title', 'index_as_target')
    # PERIODS.add_alias('manual_date_range', 'index_as_domain')

    DATES = Frame(
        [
            _title, _to_itself, _manual_date,
            _to_periods,
            _to_locations, _to_channels,
            Cl(tag='to_journals', key='📉일지'),
            Cl(tag='sync_status', key='🏁최신'),
        ]
    )
    # DATES.add_alias('title', 'index_as_target')
    # DATES.add_alias('manual_date', 'index_as_domain')

    JOURNALS = Frame(
        _AUTO_DATE,
        [
            _title, _to_itself, _timestr,
            _to_periods, _to_dates,
            _to_themes, _to_locations, _to_readings, _to_channels,
            Cl(tag='up_self', key='🧵구성'),
            Cl(tag='down_self', key='🧵요소'),
        ]
    )
    WRITINGS = Frame(
        _AUTO_DATE,
        [
            _title, _to_itself, _timestr,
            _to_periods, _to_dates, _to_journals,
            _to_readings, _to_channels,
            Cl(tag='to_themes', key='📕맥락'),
        ]
    )
    MEMOS = Frame(
        _AUTO_DATE,
        [
            _title, _to_itself,
            _to_periods, _to_dates, _to_journals,
        ]
    )
    SCHEDULES = Frame(
        _AUTO_DATE,
        [
            _title, _to_itself, _timestr,
            Cl(tag='to_periods', key='📉기간'),
            Cl(tag='to_dates', key='📉날짜'),
            Cl(tag='to_created_periods', key='📉기간'),
            Cl(tag='to_created_dates', key='📉날짜'),
            Cl(tag='to_scheduled_periods', key='🧶기간'),
            Cl(tag='to_scheduled_dates', key='🧶날짜'),
            Cl(tag='gcal_sync_status', key='🏁Gcal'),
            Cl(tag='gcal_link', key='📚Gcal'),
            Cl(tag='gcal_id', key='📚Gcal_id'),
        ]
    )

    READINGS = Frame(
        _AUTO_DATE,
        [
            _title, _to_itself,
            _to_journals,
            _to_themes, _to_channels,
            Cl(tag='to_periods', key='🧶기간_시작'),
            Cl(tag='to_dates', key='🧶날짜_시작'),
            Cl(tag='to_schedules', key='📘일정'),
            Cl(tag='status_exclude', key='🏁버킷<-경과'),
            Cl(tag='is_book', key='🔵도서<-유형'),
        ]
    )
