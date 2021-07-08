from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference, MatchorCreatebyIndex
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch

if __name__ == '__main__':
    stopwatch('클라이언트 접속')

    query = Query(GIGAN_ID)
    response = query.execute()
    gigan = PageListParser.from_query(response)

    query = Query(NALJJA_ID)
    frame = query.filter_maker.frame_by_relation(NALJJA_TO_GIGAN)
    query.push_filter(frame.is_empty())
    response = query.execute()
    naljja = PageListParser.from_query(response)

    query = Query(ILJI_ID)
    frame = query.filter_maker.frame_by_relation(ILJI_TO_GIGAN)
    query.push_filter(frame.is_empty())
    response = query.execute()
    ilji = PageListParser.from_query(response)

    query = Query(JINDO_ID)
    frame = query.filter_maker.frame_by_relation(JINDO_TO_GIGAN)
    query.push_filter(frame.is_empty())
    response = query.execute()
    jindo = PageListParser.from_query(response)

    request = MatchorCreatebyIndex(
        naljja, gigan, NALJJA_ID, NALJJA_TO_GIGAN,
        naljja_as_gigan, NALJJA_INDEX, GIGAN_INBOUND
    )
    stopwatch('날짜->기간')
    request.execute()

    request = MatchbyReference(
        ilji, gigan, ILJI_TO_GIGAN, ILJI_TO_NALJJA, NALJJA_TO_GIGAN
    )
    stopwatch('일지-(날짜)->기간')
    request.execute()

    request = MatchbyReference(
        ilji, gigan, JINDO_TO_GIGAN, JINDO_TO_NALJJA, NALJJA_TO_GIGAN
    )
    stopwatch('진도-(날짜)->기간')
    request.execute()

    stopwatch('작업 완료')

