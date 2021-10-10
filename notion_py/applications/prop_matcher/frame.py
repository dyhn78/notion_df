from notion_py.interface import TypeName

"""
날짜 관련된 formula 속성의 값은
그리니치 시간대를 기준으로 그때그때 계산하는 것 같다.
노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서 이쪽 파이썬 코드에서
처리하는 식으로 움직이자.
"""


class Frames:
    _Unit = TypeName.frame_unit
    _Frame = TypeName.frame

    _TITLE = _Unit(tag='title', key='📚제목')
    _AUTO_DATE_U = _Unit(tag='auto_date', key='날짜값⏲️')
    _AUTO_DATETIME_U = _Unit(tag='auto_datetime', key='날짜⏲️')
    _AUTO_DATE = _Frame(_AUTO_DATE_U, _AUTO_DATETIME_U)
    _AUTO_DATE.add_alias('auto_datetime', 'index_as_domain')

    _TO_PERIODS = _Unit(tag='to_periods', key='🧶기간')
    _TO_DATES = _Unit(tag='to_dates', key='🧶날짜')
    _TO_JOURNALS = _Unit(tag='to_journals', key='🧵일지')
    _TO_READINGS = _Unit(tag='to_readings', key='📒읽기')
    _TO_CHANNELS = _Unit(tag='to_channels', key='📒채널')

    PERIODS = _Frame(_TITLE,
                     _Unit(tag='to_itself', key='🔁기간'),
                     _Unit(tag='manual_date_range', key='📅날짜 범위'),
                     )
    PERIODS.add_alias('title', 'index_as_target')
    PERIODS.add_alias('manual_date_range', 'index_as_domain')

    DATES = _Frame(_TITLE,
                   _Unit(tag='to_itself', key='🔁날짜'),
                   _Unit(tag='manual_date', key='📆날짜'),
                   _Unit(tag='to_themes', key='📕수행'),
                   )
    DATES.add_alias('title', 'index_as_target')
    DATES.add_alias('manual_date', 'index_as_domain')

    JOURNALS = _Frame(_TITLE, _AUTO_DATE, _TO_READINGS, _TO_CHANNELS,
                      _Unit(tag='to_itself', key='🔁일지'),
                      _Unit(tag='to_themes', key='📕수행'),
                      _Unit(tag='up_self', key='🧵구성'),
                      _Unit(tag='down_self', key='🧵요소'),
                      )
    MEMOS = _Frame(_TITLE, _AUTO_DATE, _TO_JOURNALS,
                   _Unit(tag='to_itself', key='🔁메모'),
                   )
    WRITINGS = _Frame(_TITLE, _AUTO_DATE, _TO_JOURNALS, _TO_READINGS, _TO_CHANNELS,
                      _Unit(tag='to_itself', key='🔁쓰기'),
                      _Unit(tag='to_themes', key='📕요소'),
                      )

    for _frame in [DATES, JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_TO_PERIODS)
    for _frame in [JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_TO_DATES)
    for _frame in [MEMOS, WRITINGS]:
        _frame.append(_TO_JOURNALS)
