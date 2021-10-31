from notion_py.interface.editor.tabular import PageList


def query_within_date_range(pagelist: PageList,
                            date_index_tag: str, date_range=0):
    query = pagelist.open_query()
    if date_range:
        frame = query.make_filter.date_at(date_index_tag)
        ft = None
        if date_range == 7:
            ft = frame.within_past_week()
        elif date_range == 30:
            ft = frame.within_past_month()
        elif date_range == 365:
            ft = frame.within_past_year()
        if ft is not None:
            query.push_filter(ft)
    query.execute()


def query_danglings(pagelist: PageList, relation_tag: str):
    query = pagelist.open_query()
    frame = query.make_filter.relation_at(relation_tag)
    ft = frame.is_empty()
    query.push_filter(ft)
    query.execute()
