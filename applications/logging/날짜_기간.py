from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference
from applications.logging.naljja_to_gigan import NaljjaToGigan
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch

CHECK_ONLY_PAST_30_DAYS = True
CHECK_ONLY_PAST_365_DAYS = False

if __name__ == '__main__':
    stopwatch('클라이언트 접속')

    query = Query(GIGAN_ID)
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(GIGAN_DATE_INDEX)
        query.push_filter(frame.within_past_month())
    elif CHECK_ONLY_PAST_365_DAYS:
        frame = query.filter_maker.by_date(GIGAN_DATE_INDEX)
        query.push_filter(frame.within_past_year())
    response = query.execute()
    gigan = PageListParser.from_query(response)

    query = Query(NALJJA_ID)
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        query.push_filter(frame.within_past_month())
    elif CHECK_ONLY_PAST_365_DAYS:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        query.push_filter(frame.within_past_year())
    response = query.execute()
    naljja = PageListParser.from_query(response)

    query = Query(ILJI_ID)
    frame = query.filter_maker.by_relation(ILJI_TO_GIGAN)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        ft &= frame.within_past_month()
    elif CHECK_ONLY_PAST_365_DAYS:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    ilji = PageListParser.from_query(response)

    query = Query(JINDO_ID)
    frame = query.filter_maker.by_relation(JINDO_TO_GIGAN)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        ft &= frame.within_past_month()
    if CHECK_ONLY_PAST_365_DAYS:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query(response)

    request = NaljjaToGigan(naljja, gigan)
    stopwatch('날짜->기간')
    request.execute()

    request = MatchbyReference.default(
        ilji, naljja, ILJI_TO_GIGAN, ILJI_TO_NALJJA, NALJJA_TO_GIGAN
    )
    stopwatch('일지-(날짜)->기간')
    request.execute()

    request = MatchbyReference.default(
        jindo, naljja, JINDO_TO_GIGAN, JINDO_TO_NALJJA, NALJJA_TO_GIGAN
    )
    stopwatch('진도-(날짜)->기간')
    request.execute()

    stopwatch('작업 완료')
