# from pprint import pprint

from stopwatch import stopwatch
from parse_time_property import ParseTimeProperty
from interface.parse.databases import PageListParser
from interface.process.match import MatchorCreatebyIndex
from interface.requests.query import Query

ILJI_ID = 'bae6753c69d44ac7982e0ce929bb7b00'
NALJJA_ID = '961d1ca0a3d24a46b838ba85e710f18d'
ILJI_TO_NALJJA = '📘날짜'
ILJI_INDEX = '날짜값⏲️'
NALJJA_INDEX = None


stopwatch('클라이언트 접속')

ilji_query = Query(ILJI_ID)
frame = ilji_query.filter_maker.frame_by_relation(ILJI_TO_NALJJA)
ilji_query.push_filter(frame.is_empty())
response = ilji_query.execute()
ilji = PageListParser(response)
# pprint(response)
# pprint(ilji.list_of_items)
# breakpoint()

naljja_query = Query(NALJJA_ID)
response = naljja_query.execute()
naljja = PageListParser(response)

stopwatch('DB 받아오기')
ilji_to_naljja = MatchorCreatebyIndex(
    ilji, naljja, NALJJA_ID, ILJI_TO_NALJJA,
    lambda x: ParseTimeProperty(x['start']).dig6_and_dayname(plain=True), ILJI_INDEX, None
)

ilji_to_naljja.execute()
print(ilji_to_naljja.process_count)
stopwatch('작업 완료')

# TODO: Rollup과 Formula가 얽히면 (현재 버전의 API에서는) \
#  정보를 제대로 가져오지 못하는 것으로 드러났다. 언젠가는 고쳐질 테니 확장 루트는 계속 열어놓자.
