from .reading_page import BookReadingPage
from ..constants import ID_READINGS
from ...interface.client.deprecated import DatabaseFrameDeprecated

READING_PROPERTIES = {
    'media_type': ('🔵유형',
                   {
                       'book': ['📖단행본', '☕연속간행물', '✒학습자료']
                   }),
    'edit_status': ('🏁준비',
                    {
                        'pass': '0️⃣⛳정보 없음',
                        'append': '1️⃣📥안전하게(append)',
                        'overwrite': '2️⃣📥확실하게(overwrite)',
                        'continue': '3️⃣📥업데이트만(continue)',
                        'done': '4️⃣👤원제/표지 검정',
                        'url_missing': '5️⃣🔍링크 직접 찾기',
                        'lib_missing': '6️⃣🔍대출정보 직접 찾기',
                        'completely_done': '7️⃣⛳스크랩 완료'
                    }),
    'docx_name': '📚제목',
    'true_name': '🔍원제(검색용)',
    'subname': '📚부제',
    'url': '📚링크',
    'author': '📚만든이',
    'publisher': '📚만든곳',
    'page': '📚N(쪽+)',
    'cover_image': '📚표지',
    'link_to_contents': '📦이동',
    'location': '🔍위치',
    'not_available': '🔍대출중'
}

reading_dataframe = DatabaseFrameDeprecated(ID_READINGS, 'reads',
                                            READING_PROPERTIES, BookReadingPage)


class BookReadingQuerymaker:
    df = reading_dataframe

    @classmethod
    def query_regulars(cls, page_size=0):
        query = cls.df.make_query()
        frame = query.filter_maker.by_select(cls.df.frame['media_type'].name)
        ft = frame.equals_to_any(*cls.df.frame['media_type'].values['book'])
        frame = query.filter_maker.by_select(cls.df.frame['edit_status'].name)
        ft_status = frame.equals_to_any(
            *[cls.df.frame['edit_status'].values[key]
              for key in ['append', 'overwrite', 'continue']])
        ft_status |= frame.is_empty()
        ft &= ft_status
        ft &= frame.does_not_equal(cls.df.frame['edit_status'].values['done'])
        query.push_filter(ft)
        pagelist = cls.df.send_query_deprecated(query, page_size=page_size)
        # TODO > pagelist.retrieve_childrens()
        return pagelist

    @classmethod
    def query_for_library_resets(cls, page_size=0):
        query = cls.df.make_query()
        frame = query.filter_maker.by_select(cls.df.frame['media_type'].name)
        ft = frame.equals_to_any(*cls.df.frame['media_type'].values)
        frame = query.filter_maker.by_select(cls.df.frame['edit_status'].name)
        ft &= frame.equals_to_any(
            *[cls.df.frame['edit_status'].values[key]
              for key in ['url_missing', 'lib_missing']])
        # frame = query.filter_maker.by_checkbox(
        #      cls.df._unit.dataframe.props['not_available'].name)
        # ft |= frame.equals(True)
        query.push_filter(ft)
        pagelist = cls.df.send_query_deprecated(query, page_size=page_size)
        return pagelist
