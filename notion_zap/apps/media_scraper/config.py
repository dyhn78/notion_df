from notion_zap.cli.structs import PropertyColumn as Cl, PropertyFrame

ReadingDB_FRAME = PropertyFrame([
    Cl(key='📘유형', tag='media_type',
       marks_on_value={
           'book': ['📖단행본', '☕연속간행물', '✒학습자료']
       }),
    Cl(key='📘도서<-유형', tag='is_book'),
    Cl(key='🏁준비', tag='edit_status',
       labels={
           'pass': '0️⃣⛳정보 없음',
           'append': '1️⃣📥안전하게(append)',
           'overwrite': '2️⃣📥확실하게(overwrite)',
           'continue': '3️⃣📥업데이트만(continue)',
           'tentatively_done': '4️⃣👤원제/표지 검정',
           'url_missing': '5️⃣❓링크 직접 찾기',
           'lib_missing': '6️⃣❓대출정보 직접 찾기',
           'completely_done': '7️⃣⛳스크랩 완료'
       },
       marks_on_label={
           'regular_scraps': ['append', 'overwrite', 'continue'],
           'need_resets': ['url_missing', 'lib_missing'],
           'done': ['tentatively_done', 'completely_done'],
       }),
    Cl(key='📚제목', tag='docx_name'),
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
ReadingDB_FRAME.add_alias('docx_name', 'title')
