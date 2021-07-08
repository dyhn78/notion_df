from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference, MatchorCreatebyIndex
from applications.logging.naljja_to_gigan import NaljjaToGigan
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch

if __name__ == '__main__':
    stopwatch('클라이언트 접속')

    query = Query(GIGAN_ID)
    response = query.execute(page_size=0)
    gigan = PageListParser.from_query(response)

    query = Query(NALJJA_ID)
    frame = query.filter_maker.frame_by_relation(NALJJA_TO_GIGAN)
    # query.push_filter(frame.is_empty())
    response = query.execute(page_size=0)
    naljja = PageListParser.from_query(response)

    query = Query(ILJI_ID)
    frame = query.filter_maker.frame_by_relation(ILJI_TO_GIGAN)
    # query.push_filter(frame.is_empty())
    response = query.execute(page_size=0)
    ilji = PageListParser.from_query(response)

    query = Query(JINDO_ID)
    frame = query.filter_maker.frame_by_relation(JINDO_TO_GIGAN)
    # query.push_filter(frame.is_empty())
    response = query.execute(page_size=0)
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
