from notion_py.applications.read_scraper.reading_dataframe import BookReadingQuerymaker
from notion_py.utility import stopwatch


def reset_status_for_books(page_size=0):
    pagelist = BookReadingQuerymaker.query_for_library_resets(page_size=page_size)
    for page in pagelist.values:
        page.props.set_overwrite(True)
        page.props.write.select(page.PROP_NAME['edit_status'], page.EDIT_STATUS['append'])
        page.props.write.checkbox(page.PROP_NAME['not_available'], False)
        page.execute()
    stopwatch('작업 완료')
