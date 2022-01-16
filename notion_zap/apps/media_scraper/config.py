from notion_zap.cli.structs import PropertyColumn as Cl, PropertyFrame

READING_FRAME = PropertyFrame([
    Cl(key='📘유형', tag='media_type',
       marks_on_value={
           'book': ['📖단행본', '☕연속간행물', '✒학습자료']
       }),
    Cl(key='📘도서<-유형', tag='is_book'),
    Cl(key='🏁준비', tag='edit_status',
       labels={
           'append': '📥본문(비파괴)/위치',
           'overwrite': '📥본문(파괴)/위치',
           'continue': '📥위치만',

           'completely_done': '⛳수합 완료',
           'pass': '⭕정보 없음',

           'tentatively_done': '👤원제/표지 검정',
           'manually_filled': '👤직접 채워넣기',

           'url_missing': '❓링크 찾기',
           'lib_missing': '❓위치 찾기',
       },
       marks_on_label={
           'regular_scraps': ['append', 'overwrite', 'continue'],
           'need_resets': ['url_missing', 'lib_missing'],
           'done': ['pass', 'tentatively_done', 'completely_done', 'manually_filled'],
           'cannot_overwrite': ['append', 'continue']
       }),
    Cl(key='📚제목', tags=['docx_name', 'title']),
    Cl(key='📚원제(검색용)', tag='true_name'),
    Cl(key='📚부제', tag='subname'),
    Cl(key='📚링크', tag='url'),
    Cl(key='📚만든이', tag='author'),
    Cl(key='📚만든곳', tag='publisher'),
    Cl(key='📚N(쪽+)', tag='volume'),
    Cl(key='📚표지', tag='cover_image'),
    Cl(key='📚위치', tag='location'),
    Cl(key='📚대출중', tag='not_available'),
    Cl(key='📦이동', tag='link_to_contents'),
])
