from applications.logging.parse_time_property import ParseTimeProperty


def formatting_as_naljja(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_dig6_and_weekday()


def formatting_as_gigan(x):
    return ParseTimeProperty(x['start'], plain_date=True).strf_year_and_week()


NALJJA_ID = '961d1ca0a3d24a46b838ba85e710f18d'
ILJI_ID = 'bae6753c69d44ac7982e0ce929bb7b00'
JINDO_ID = 'c8d46c01d6c941a9bf8df5d115a05f03'
GIGAN_ID = 'd020b399cf5947a59d11a0b9e0ea45d0'
SSEUGI_ID = '069bbebd632f4a6ea3044575a064cf0f'

TO_GIGAN = '🧶기간'
TO_NALJJA = '🧶날짜'
TO_ILJI = '🧵일지'

GIGAN_DATE_INDEX = '📅날짜 범위'
NALJJA_DATE_INDEX = '📆날짜'
ILJI_DATE_INDEX = JINDO_DATE_INDEX = SSEUGI_DATE_INDEX = '날짜⏲️'
NALJJA_TITLE_INBOUND = GIGAN_TITLE_INBOUND = '📚제목'

as_naljja = formatting_as_naljja
# as_gigan = formatting_as_gigan()
