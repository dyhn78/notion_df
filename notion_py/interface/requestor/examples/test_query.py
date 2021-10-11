# import os
# from notion_client import AsyncClient, Client
#
# from notion_py.interface.requestor.query import Query
# from notion_py.interface.utility import stopwatch
#
#
# os.environ['NOTION_TOKEN'] = ***REMOVED***
#
# ASYNC = False
#
# if ASYNC:
#     notion = AsyncClient(auth=os.environ['NOTION_TOKEN'])
# else:
#     notion = Client(auth=os.environ['NOTION_TOKEN'])
#
# stopwatch('클라이언트 접속')
#
# TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"
#
# test_database = notion.databases.retrieve()
# test_db_query_maker = Query(TEST_DATABASE_ID)
#
# name_frame = test_db_query_maker.make_filter.text_of('이름')
# filter1 = name_frame.starts_with('2')
# filter2 = name_frame.ends_with('0')
# test_filter = (filter1 & filter2)
# test_db_query_maker.push_filter(test_filter)
# # pprint(test_filter.apply)
#
# test_db_query_maker.sort.append_ascending('이름')
# # pprint(test_db_query_maker.sort.apply)
#
# test_subpages = test_db_query_maker.execute()
# # pprint(test_subpages)
#
# # plain_items = PageListParser.from_query_response(test_subpages).list_of_items
# # pprint(plain_items)
#
# stopwatch('작업 완료')
