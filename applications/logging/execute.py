from applications.logging.match_by_date_index import *
from applications.logging.match_property import MatchbyReference, MatchorCreatebyIndex


def base_function(x):
    return ParseTimeProperty(x).dig6_and_dayname(plain=True)


ILJI_ID = 'bae6753c69d44ac7982e0ce929bb7b00'
NALJJA_ID = '961d1ca0a3d24a46b838ba85e710f18d'
JINDO_ID = 'c8d46c01d6c941a9bf8df5d115a05f03'

ILJI_TO_NALJJA = JINDO_TO_NALJJA = '📘날짜'
JINDO_TO_ILJI = '🧵일지'
ILJI_INDEX = JINDO_INDEX = '날짜⏲️'
NALJJA_INDEX = None
ilji_function = jindo_function = base_function


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

stopwatch('DB 받아오기')
ilji_to_naljja = MatchorCreatebyIndex(
    ilji, naljja, NALJJA_ID, ILJI_TO_NALJJA,
    ilji_function, ILJI_INDEX, None
)
jindo_to_naljja_by_ilji = MatchbyReference(
    jindo, ilji, JINDO_TO_NALJJA, JINDO_TO_ILJI, ILJI_TO_NALJJA
)

ilji_to_naljja.execute()
stopwatch('*'*30)

jindo = jindo_to_naljja_by_ilji.execute(reprocess_outside=True)
stopwatch('*'*30)

jindo_to_naljja_by_index = MatchorCreatebyIndex(
    jindo, naljja, NALJJA_ID, JINDO_TO_NALJJA,
    jindo_function, JINDO_INDEX, None
)
jindo_to_naljja_by_index.execute()

stopwatch('작업 완료')
