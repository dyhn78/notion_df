from notion_zap.cli.struct import PropertyColumn as Cl, PropertyFrame

ReadingDB_FRAME = PropertyFrame([
    Cl('🔵유형', 'media_type',
       value_groups_by_key={
           'book': ['📖단행본', '☕연속간행물', '✒학습자료']
       }),
    Cl('🔵도서<-유형', 'is_book'),
    Cl('🏁준비', 'edit_status',
       values={
           'pass': '0️⃣⛳정보 없음',
           'append': '1️⃣📥안전하게(append)',
           'overwrite': '2️⃣📥확실하게(overwrite)',
           'continue': '3️⃣📥업데이트만(continue)',
           'done': '4️⃣👤원제/표지 검정',
           'url_missing': '5️⃣🔍링크 직접 찾기',
           'lib_missing': '6️⃣🔍대출정보 직접 찾기',
           'completely_done': '7️⃣⛳스크랩 완료'
       },
       value_groups_by_tag={
           'routines': ['append', 'overwrite', 'continue'],
           'need_resets': ['url_missing', 'lib_missing'],
           'done': ['done', 'completely_done']
       },
       value_infos_by_tag={'append': (False, False),
                           'continue': (False, False),
                           'overwrite': (True, True)}
       ),
    Cl('📚제목', 'docx_name'),
    Cl('📚원제(검색용)', 'true_name'),
    Cl('📚부제', 'subname'),
    Cl('📚링크', 'url'),
    Cl('📚만든이', 'author'),
    Cl('📚만든곳', 'publisher'),
    Cl('📚N(쪽+)', 'volume'),
    Cl('📚표지', 'cover_image'),
    Cl('📦이동', 'link_to_contents'),
    Cl('📚위치', 'location'),
    Cl('📚대출중', 'not_available'),
])
ReadingDB_FRAME.add_alias('docx_name', 'title')
