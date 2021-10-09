from notion_py.interface import TypeName


class QueryMaker:
    def __init__(self, date_range: int):
        self.date_range = date_range

    def query_as_parents(self, pagelist: TypeName.pagelist,
                         key_at_date_index: str):
        query_form = pagelist.query
        if self.date_range:
            frame = query_form.make_filter.date_at(key_at_date_index)
            ft = None
            if self.date_range == 7:
                ft = frame.within_past_week()
            elif self.date_range == 30:
                ft = frame.within_past_month()
            elif self.date_range == 365:
                ft = frame.within_past_year()
            query_form.push_filter(ft)
        pagelist.run_query()

    def query_as_children(self, pagelist: TypeName.pagelist,
                          date_index: str, dom_to_tar: str):
        query_form = pagelist.query
        frame = query_form.make_filter.relation_at(dom_to_tar)
        ft = frame.is_empty()
        if self.date_range:
            frame = query_form.make_filter.date_at(date_index)
            if self.date_range == 7:
                ft &= frame.within_past_week()
            elif self.date_range == 30:
                ft &= frame.within_past_month()
            elif self.date_range == 365:
                ft &= frame.within_past_year()
        query_form.push_filter(ft)
        pagelist.run_query()
