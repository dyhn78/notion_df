from notion_py.helpers import stopwatch
from notion_py.interface.read import Query
from ..constant_page_ids import ILGGI_ID
from .regular_writing import ReadingPageList, ReadingPage


def reset_library_status(page_size=0):
    pagelist = query_books(page_size=page_size)
    for page in pagelist.values:
        page.props.set_overwrite(True)
        page.props.write.select(page.PROP_NAME['edit_status'], page.EDIT_STATUS['append'])
        page.props.write.checkbox(page.PROP_NAME['not_available'], False)
        page.execute()
    stopwatch('작업 완료')


def query_books(page_size=0) -> ReadingPageList:
    query = Query(ILGGI_ID)
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['media_type'])
    ft = frame.equals_to_any(*ReadingPage.MEDIA_TYPES)
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['edit_status'])
    ft &= frame.equals(ReadingPage.EDIT_STATUS['done'])
    frame = query.filter_maker.by_checkbox(ReadingPage.PROP_NAME['not_available'])
    ft &= frame.equals(True)
    query.push_filter(ft)
    return ReadingPageList.from_query(query, page_size=page_size)
