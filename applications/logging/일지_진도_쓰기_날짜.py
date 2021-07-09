from pprint import pprint

from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference, MatchorCreatebyIndex
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch

CHECK_ONLY_PAST_30_DAYS = True

if __name__ == '__main__':
    stopwatch('클라이언트 접속')

    query = Query(NALJJA_ID)
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        query.push_filter(frame.within_past_month())
    response = query.execute()
    naljja = PageListParser.from_query(response)

    query = Query(ILJI_ID)
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        query.push_filter(frame.within_past_month())
    response = query.execute()
    ilji = PageListParser.from_query(response)

    query = Query(JINDO_ID)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query(response)

    query = Query(SSEUGI_ID)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_30_DAYS:
        frame = query.filter_maker.by_date(SSEUGI_DATE_INDEX)
        ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    sseugi = PageListParser.from_query(response)

    request = MatchorCreatebyIndex.default(
        ilji, naljja, NALJJA_ID, TO_NALJJA,
        ILJI_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('일지->날짜')
    request.execute()

    request = MatchbyReference.default(
        jindo, ilji, TO_NALJJA, TO_ILJI, TO_NALJJA
    )
    stopwatch('진도-(일지)->날짜')
    jindo = request.execute(reprocess_outside=True)

    request = MatchorCreatebyIndex.default(
        jindo, naljja, NALJJA_ID, TO_NALJJA,
        JINDO_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('진도-(x)->날짜')
    request.execute()

    request = MatchbyReference.default(
        sseugi, ilji, TO_NALJJA, TO_ILJI, TO_NALJJA
    )
    stopwatch('쓰기-(일지)->날짜')
    sseugi = request.execute(reprocess_outside=True)

    request = MatchorCreatebyIndex.default(
        sseugi, naljja, NALJJA_ID, TO_NALJJA,
        SSEUGI_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('쓰기-(x)->날짜')
    request.execute()

    stopwatch('작업 완료')
