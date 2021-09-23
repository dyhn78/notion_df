from notion_py.interface import TypeName


class Frames:
    _Unit = TypeName.frame_unit
    _Frame = TypeName.frame

    _TITLE = _Unit(key='title', name='📚제목')
    _AUTO_DATE_U = _Unit(key='auto_date', name='날짜값⏲️')
    _AUTO_DATETIME_U = _Unit(key='auto_datetime', name='날짜⏲️')
    _AUTO_DATE = _Frame(_AUTO_DATE_U, _AUTO_DATETIME_U)
    _AUTO_DATE.add_alias('auto_datetime', 'index_as_domain')
    """날짜값 속성은 무슨 그리니치 시간대를 기준으로 받아오는 건지,
    노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
    웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서 이쪽 파이썬 코드에서
    처리하는 식으로 움직이자.
    """

    _TO_PERIODS = _Unit(key='to_periods', name='🧶기간')
    _TO_DATES = _Unit(key='to_dates', name='🧶날짜')
    _TO_JOURNALS = _Unit(key='to_journals', name='🧵일지')
    # _TO_SHOTS = _Unit(key='to_shots', name='🧵진도')
    _TO_READINGS = _Unit(key='to_readings', name='📒읽기')
    _TO_CHANNELS = _Unit(key='to_channels', name='📒채널')

    PERIODS = _Frame(_TITLE,
                     _Unit(key='manual_date_range', name='📅날짜 범위'),
                     _Unit(key='self_ref', name='🔁기간'))
    PERIODS.add_alias('title', 'index_as_target')
    PERIODS.add_alias('manual_date_range', 'index_as_domain')

    DATES = _Frame(_TITLE,
                   _Unit(key='manual_date', name='📆날짜'),
                   _Unit(key='self_ref', name='🔁날짜'))
    DATES.add_alias('title', 'index_as_target')
    DATES.add_alias('manual_date', 'index_as_domain')
    """
    JOURNALS = _Frame(_TITLE, _AUTO_DATE,
                      _Unit(key='self_ref', name='🔁일지'))
    """
    JOURNALS = _Frame(_TITLE, _AUTO_DATE,
                      _TO_READINGS, _TO_CHANNELS,
                      _Unit(key='to_themes', name='📕수행'),
                      _Unit(key='self_ref', name='🔁일지'))
    MEMOS = _Frame(_TITLE, _AUTO_DATE, _TO_JOURNALS,
                   _Unit(key='self_ref', name='🔁메모'))
    WRITINGS = _Frame(_TITLE, _AUTO_DATE, _TO_JOURNALS,
                      _TO_READINGS, _TO_CHANNELS,
                      _Unit(key='to_themes', name='📉수행'),
                      _Unit(key='self_ref', name='🔁쓰기'))

    for _frame in [DATES, JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_TO_PERIODS)
    for _frame in [JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_TO_DATES)
    for _frame in [MEMOS, WRITINGS]:
        _frame.append(_TO_JOURNALS)
