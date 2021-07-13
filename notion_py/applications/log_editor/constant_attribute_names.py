from .parse_time_property import ParseTimeProperty
from ..constant_page_ids import *


def formatting_as_naljja(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_dig6_and_weekday()


def formatting_as_gigan(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_year_and_week()


TO_GIGAN = '🧶기간'
TO_NALJJA = '🧶날짜'
TO_ILJI = '🧵일지'

GIGAN_DATE_INDEX = '📅날짜 범위'
NALJJA_DATE_INDEX = '📆날짜'
ILJI_DATE_INDEX = JINDO_DATE_INDEX = SSEUGI_DATE_INDEX = '날짜⏲️'
NALJJA_TITLE_INBOUND = GIGAN_TITLE_INBOUND = '📚제목'

as_naljja = formatting_as_naljja
# as_gigan = formatting_as_gigan()
