from pprint import pprint

from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference, MatchorCreatebyIndex
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch
from applications.logging.naljja_to_gigan import NaljjaToGigan


def connect_to_naljja():
    stopwatch('클라이언트 접속')

    query = Query(NALJJA_ID)
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            query.push_filter(frame.within_past_week())
        if CHECK_ONLY_PAST_X_DAYS == 30:
            query.push_filter(frame.within_past_month())
    response = query.execute()
    naljja = PageListParser.from_query(response)

    query = Query(ILJI_ID)
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            query.push_filter(frame.within_past_week())
        if CHECK_ONLY_PAST_X_DAYS == 30:
            query.push_filter(frame.within_past_month())
    response = query.execute()
    ilji = PageListParser.from_query(response)

    request = MatchorCreatebyIndex.default(
        ilji, naljja, NALJJA_ID, TO_NALJJA,
        ILJI_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('일지->날짜')
    request.execute()

    query = Query(JINDO_ID)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            ft &= frame.within_past_week()
        if CHECK_ONLY_PAST_X_DAYS == 30:
            ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query(response)

    query = Query(SSEUGI_ID)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(SSEUGI_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            ft &= frame.within_past_week()
        if CHECK_ONLY_PAST_X_DAYS == 30:
            ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    sseugi = PageListParser.from_query(response)

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


def connect_to_gigan():
    stopwatch('클라이언트 접속')

    query = Query(GIGAN_ID)
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(GIGAN_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            query.push_filter(frame.within_past_week())
        elif CHECK_ONLY_PAST_X_DAYS == 30:
            query.push_filter(frame.within_past_month())
        elif CHECK_ONLY_PAST_X_DAYS == 365:
            query.push_filter(frame.within_past_year())
    response = query.execute()
    gigan = PageListParser.from_query(response)

    query = Query(NALJJA_ID)
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            query.push_filter(frame.within_past_week())
        elif CHECK_ONLY_PAST_X_DAYS == 30:
            query.push_filter(frame.within_past_month())
        elif CHECK_ONLY_PAST_X_DAYS == 365:
            query.push_filter(frame.within_past_year())
    response = query.execute()
    naljja = PageListParser.from_query(response)

    request = NaljjaToGigan(naljja, gigan)
    stopwatch('날짜->기간')
    request.execute()

    query = Query(ILJI_ID)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            ft &= frame.within_past_week()
        elif CHECK_ONLY_PAST_X_DAYS == 30:
            ft &= frame.within_past_month()
        elif CHECK_ONLY_PAST_X_DAYS == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    ilji = PageListParser.from_query(response)

    query = Query(JINDO_ID)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            ft &= frame.within_past_week()
        elif CHECK_ONLY_PAST_X_DAYS == 30:
            ft &= frame.within_past_month()
        elif CHECK_ONLY_PAST_X_DAYS == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query(response)

    query = Query(SSEUGI_ID)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if CHECK_ONLY_PAST_X_DAYS:
        frame = query.filter_maker.by_date(SSEUGI_DATE_INDEX)
        if CHECK_ONLY_PAST_X_DAYS == 7:
            ft &= frame.within_past_week()
        elif CHECK_ONLY_PAST_X_DAYS == 30:
            ft &= frame.within_past_month()
        elif CHECK_ONLY_PAST_X_DAYS == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    sseugi = PageListParser.from_query(response)

    request = MatchbyReference.default(
        ilji, naljja, TO_GIGAN, TO_NALJJA, TO_GIGAN
    )
    stopwatch('일지-(날짜)->기간')
    request.execute()

    request = MatchbyReference.default(
        jindo, naljja, TO_GIGAN, TO_NALJJA, TO_GIGAN
    )
    stopwatch('진도-(날짜)->기간')
    request.execute()

    request = MatchbyReference.default(
        sseugi, naljja, TO_GIGAN, TO_NALJJA, TO_GIGAN
    )
    stopwatch('쓰기-(날짜)->기간')
    request.execute()
    stopwatch('작업 완료')


CHECK_ONLY_PAST_X_DAYS = 7

connect_to_naljja()
connect_to_gigan()
