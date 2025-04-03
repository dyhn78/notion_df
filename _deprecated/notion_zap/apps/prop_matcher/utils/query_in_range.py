from notion_zap.cli import blocks


def query_within_date_range(pagelist: blocks.RowChildren,
                            date_index_tag: str, date_range=0):
    query = pagelist.open_query()
    if date_range:
        frame = query.filter_manager_by_tags.date(date_index_tag)
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
