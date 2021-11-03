from notion_py.interface.common import \
    PropertyFrame as Frame, PropertyFrameUnit as Unit

"""
날짜 관련된 formula 속성의 값은
그리니치 시간대를 기준으로 그때그때 계산하는 것 같다.
노션 클라이언트에 뜨는 값과 API로 받아오는 값이 다르다.
웬만하면 노션 날짜 수식을 믿지 말고, raw data를 가져와서 이쪽 파이썬 코드에서
처리하는 식으로 움직이자.
"""


class MatchFrames:
    _title = Unit(tag='title', key='📚제목')
    _auto_date = Unit(tag='auto_date', key='날짜값⏲️')
    _auto_datetime = Unit(tag='auto_datetime', key='날짜⏲️')
    _AUTO_DATE = Frame([_auto_date, _auto_datetime])
    _AUTO_DATE.add_alias('auto_datetime', 'index_as_domain')

    _to_periods = Unit(tag='to_periods', key='🧶기간')
    _to_dates = Unit(tag='to_dates', key='🧶날짜')
    _to_journals = Unit(tag='to_journals', key='🧵일지')
    _to_readings = Unit(tag='to_readings', key='📒읽기')
    _to_channels = Unit(tag='to_channels', key='📒채널')

    PERIODS = Frame([_title,
                     Unit(tag='to_itself', key='🔁기간'),
                     Unit(tag='manual_date_range', key='📅날짜 범위'),
                     ])
    PERIODS.add_alias('title', 'index_as_target')
    PERIODS.add_alias('manual_date_range', 'index_as_domain')

    DATES = Frame([_title,
                   Unit(tag='to_itself', key='🔁날짜'),
                   Unit(tag='manual_date', key='🕧날짜'),
                   Unit(tag='to_themes', key='📕수행'),
                   ])
    DATES.add_alias('title', 'index_as_target')
    DATES.add_alias('manual_date', 'index_as_domain')

    JOURNALS = Frame(_AUTO_DATE,
                     [_title, _to_readings, _to_channels,
                      Unit(tag='to_itself', key='🔁일지'),
                      Unit(tag='to_themes', key='📕수행'),
                      Unit(tag='up_self', key='🧵구성'),
                      Unit(tag='down_self', key='🧵요소'),
                      ])
    MEMOS = Frame(_AUTO_DATE,
                  [_title, _to_journals,
                   Unit(tag='to_itself', key='🔁메모'),
                   ])
    WRITINGS = Frame(_AUTO_DATE,
                     [_title, _to_journals, _to_readings, _to_channels,
                      Unit(tag='to_itself', key='🔁쓰기'),
                      Unit(tag='to_themes', key='📕맥락'),
                      ])

    for _frame in [DATES, JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_to_periods)
    for _frame in [JOURNALS, MEMOS, WRITINGS]:
        _frame.append(_to_dates)
    for _frame in [MEMOS, WRITINGS]:
        _frame.append(_to_journals)
