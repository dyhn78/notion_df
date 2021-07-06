# from pprint import pprint

from stopwatch import stopwatch
from parse_time_property import ParseTimeProperty
from interface.parse.databases import PageListParser
from applications.logging.match_property import MatchorCreatebyIndex
from interface.requests.query import Query


def match_or_create_by_date_index(domain_id, target_id, domain_to_target, domain_index):
    # TODO: Rollup과 Formula가 얽히면 (현재 버전의 API에서는) \
    #  정보를 제대로 가져오지 못하는 것으로 드러났다. 언젠가는 고쳐질 테니 확장 루트는 계속 열어놓자.
    stopwatch('클라이언트 접속')

    domain_query = Query(domain_id)
    frame = domain_query.filter_maker.frame_by_relation(domain_to_target)
    domain_query.push_filter(frame.is_empty())
    response = domain_query.execute()
    domain = PageListParser(response)

    target_query = Query(target_id)
    response = target_query.execute()
    target = PageListParser(response)

    stopwatch('DB 받아오기')
    processing = MatchorCreatebyIndex(
        domain, target, target_id, domain_to_target,
        lambda x: ParseTimeProperty(x['start']).dig6_and_dayname(plain=True), domain_index, None
    )
    processing.execute()
    print(processing.process_count)
    stopwatch('작업 완료')
