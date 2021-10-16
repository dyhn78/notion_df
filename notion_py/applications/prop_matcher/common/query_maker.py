from notion_py.interface.editor.tabular import PageList


class QueryMaker:
    def __init__(self, date_range: int):
        self.date_range = date_range

    def query_as_parents(self, pagelist: PageList,
                         key_at_date_index: str):
        query = pagelist.open_query()
        if self.date_range:
            frame = query.make_filter.date_at(key_at_date_index)
            ft = None
            if self.date_range == 7:
                ft = frame.within_past_week()
            elif self.date_range == 30:
                ft = frame.within_past_month()
            elif self.date_range == 365:
                ft = frame.within_past_year()
            query.push_filter(ft)
        query.execute()

    def query_as_children(self, pagelist: PageList,
                          date_index: str, dom_to_tar: str):
        query = pagelist.open_query()
        frame = query.make_filter.relation_at(dom_to_tar)
        ft = frame.is_empty()
        if self.date_range:
            frame = query.make_filter.date_at(date_index)
            if self.date_range == 7:
                ft &= frame.within_past_week()
            elif self.date_range == 30:
                ft &= frame.within_past_month()
            elif self.date_range == 365:
                ft &= frame.within_past_year()
        query.push_filter(ft)
        query.execute()
