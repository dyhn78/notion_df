from filter_maker import QueryFilterFrameMaker as FilterFrameMaker
from sorts_maker import QuerySorts as Sorts
from db_reader import DatabaseRetrieveReader as DBRetrieveReader


class QueryMaker:
    def __init__(self, retrieve_reader: DBRetrieveReader):
        self.filter = FilterFrameMaker(retrieve_reader)
        self.sorts = Sorts()

