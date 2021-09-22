from notion_py.applications_depr.read_scraper.reading_dataframe import BookReadingQuerymaker
from notion_py.interface.utility import stopwatch


def reset_status_for_books(page_size=0):
    pagelist = BookReadingQuerymaker.query_for_library_resets(page_size=page_size)
    for page in pagelist.pagelist:
        page.props.set_overwrite(True)
        page.props.write.select(page.PROP_NAME['edit_status'], page.EDIT_STATUS['append'])
        page.props.write.checkbox(page.PROP_NAME['not_available'], False)
        page.fetch_children()
    stopwatch('작업 완료')
