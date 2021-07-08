from interface.parse.databases import PageListParser
from interface.requests.query import Query
from applications.process.match_property import MatchbyReference, MatchorCreatebyIndex
from applications.logging.constants import *
from applications.helpers.stopwatch import stopwatch


if __name__ == '__main__':
    stopwatch('클라이언트 접속')

    naljja_query = Query(NALJJA_ID)
    naljja_response = naljja_query.execute()
    naljja = PageListParser.from_query(naljja_response)

    ilji_query = Query(ILJI_ID)
    ilji_response = ilji_query.execute()
    ilji = PageListParser.from_query(ilji_response)

    jindo_query = Query(JINDO_ID)
    frame = jindo_query.filter_maker.frame_by_relation(ILJI_TO_NALJJA)
    jindo_query.push_filter(frame.is_empty())
    jindo_response = jindo_query.execute()
    jindo = PageListParser.from_query(jindo_response)

    request = MatchorCreatebyIndex(
        ilji, naljja, NALJJA_ID, ILJI_TO_NALJJA,
        ilji_as_naljja, ILJI_INDEX, NALJJA_INBOUND
    )
    stopwatch('일지->날짜')
    request.execute()

    request = MatchbyReference(
        jindo, ilji, JINDO_TO_NALJJA, JINDO_TO_ILJI, ILJI_TO_NALJJA
    )
    stopwatch('진도-(일지)->날짜')
    jindo = request.execute(reprocess_outside=True)

    request = MatchorCreatebyIndex(
        jindo, naljja, NALJJA_ID, JINDO_TO_NALJJA,
        jindo_as_naljja, JINDO_INDEX, NALJJA_INBOUND
    )
    stopwatch('진도-(x)->날짜')
    request.execute()

    stopwatch('작업 완료')
