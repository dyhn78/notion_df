# from pprint import pprint
from notion_py.applications.constant_page_ids import ID_DATES, ID_JOURNALS, ID_CHECKPOINTS, ID_PERIODS, ID_WRITINGS
from notion_py.interface.parse import PageListParser
from notion_py.interface.read import Query
from notion_py.helpers.stopwatch import stopwatch
from notion_py.applications.log_editor.match_property import MatchbyReference, MatchorCreatebyIndex
from notion_py.applications.log_editor.class_naljja_to_gigan import NaljjaToGigan
from notion_py.applications.log_editor.constant_attribute_names import *


def connect_to_naljja(check_only_past_x_days = 0):
    query = Query(ID_DATES)
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        if check_only_past_x_days == 7:
            query.push_filter(frame.within_past_week())
        if check_only_past_x_days == 30:
            query.push_filter(frame.within_past_month())
    response = query.execute()
    naljja = PageListParser.from_query_response(response)

    query = Query(ID_JOURNALS)
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        if check_only_past_x_days == 7:
            query.push_filter(frame.within_past_week())
        if check_only_past_x_days == 30:
            query.push_filter(frame.within_past_month())
    response = query.execute()
    ilji = PageListParser.from_query_response(response)

    request = MatchorCreatebyIndex.default(
        ilji, naljja, ID_DATES, TO_NALJJA,
        ILJI_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('일지->날짜')
    request.execute()

    query = Query(ID_CHECKPOINTS)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        if check_only_past_x_days == 7:
            ft &= frame.within_past_week()
        if check_only_past_x_days == 30:
            ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query_response(response)

    query = Query(ID_WRITINGS)
    frame = query.filter_maker.by_relation(TO_NALJJA)
    ft = frame.is_empty()
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(SSEUGI_DATE_INDEX)
        if check_only_past_x_days == 7:
            ft &= frame.within_past_week()
        if check_only_past_x_days == 30:
            ft &= frame.within_past_month()
    query.push_filter(ft)
    response = query.execute()
    sseugi = PageListParser.from_query_response(response)

    request = MatchbyReference.default(
        jindo, ilji, TO_NALJJA, TO_ILJI, TO_NALJJA
    )
    stopwatch('진도-(일지)->날짜')
    jindo = request.execute(reprocess_outside=True)

    request = MatchorCreatebyIndex.default(
        jindo, naljja, ID_DATES, TO_NALJJA,
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
        sseugi, naljja, ID_DATES, TO_NALJJA,
        SSEUGI_DATE_INDEX, NALJJA_TITLE_INBOUND, as_naljja
    )
    stopwatch('쓰기-(x)->날짜')
    request.execute()

    stopwatch('작업 완료')


def connect_to_gigan(check_only_past_x_days = 0):
    query = Query(ID_PERIODS)
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(GIGAN_DATE_INDEX)
        if check_only_past_x_days == 7:
            query.push_filter(frame.within_past_week())
        elif check_only_past_x_days == 30:
            query.push_filter(frame.within_past_month())
        elif check_only_past_x_days == 365:
            query.push_filter(frame.within_past_year())
    response = query.execute()
    gigan = PageListParser.from_query_response(response)

    query = Query(ID_DATES)
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(NALJJA_DATE_INDEX)
        if check_only_past_x_days == 7:
            query.push_filter(frame.within_past_week())
        elif check_only_past_x_days == 30:
            query.push_filter(frame.within_past_month())
        elif check_only_past_x_days == 365:
            query.push_filter(frame.within_past_year())
    response = query.execute()
    naljja = PageListParser.from_query_response(response)

    request = NaljjaToGigan(naljja, gigan)
    stopwatch('날짜->기간')
    request.execute()

    query = Query(ID_JOURNALS)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(ILJI_DATE_INDEX)
        if check_only_past_x_days == 7:
            ft &= frame.within_past_week()
        elif check_only_past_x_days == 30:
            ft &= frame.within_past_month()
        elif check_only_past_x_days == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    ilji = PageListParser.from_query_response(response)

    query = Query(ID_CHECKPOINTS)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(JINDO_DATE_INDEX)
        if check_only_past_x_days == 7:
            ft &= frame.within_past_week()
        elif check_only_past_x_days == 30:
            ft &= frame.within_past_month()
        elif check_only_past_x_days == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    jindo = PageListParser.from_query_response(response)

    query = Query(ID_WRITINGS)
    frame = query.filter_maker.by_relation(TO_GIGAN)
    ft = frame.is_empty()
    if check_only_past_x_days:
        frame = query.filter_maker.by_date(SSEUGI_DATE_INDEX)
        if check_only_past_x_days == 7:
            ft &= frame.within_past_week()
        elif check_only_past_x_days == 30:
            ft &= frame.within_past_month()
        elif check_only_past_x_days == 365:
            ft &= frame.within_past_year()
    query.push_filter(ft)
    response = query.execute()
    sseugi = PageListParser.from_query_response(response)

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
