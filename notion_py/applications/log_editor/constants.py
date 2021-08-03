from .parse_time_property import ParseTimeProperty


TO_PERIODS = '🧶기간'
TO_DATES = '🧶날짜'
TO_JOURNALS = '🧵일지'

PERIODS_INDEX = '📅날짜 범위'
DATES_INDEX = '📆날짜'
DOMAINS_INDEX = '날짜⏲️'  # 일지, 진도, 쓰기
TITLE_PROPERTY = '📚제목'  # 날짜, 기간


def formatting_as_naljja(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_dig6_and_weekday()


def formatting_as_gigan(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_year_and_week()


as_naljja = formatting_as_naljja
# as_gigan = formatting_as_gigan()
