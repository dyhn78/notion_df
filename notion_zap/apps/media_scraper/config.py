from notion_zap.cli.structs import (
    PropertyColumn as Cl, PropertyMarkedValue as Lb, PropertyFrame)

_STATUS_MARKS = [
    Lb('📥본문(비파괴)/위치', 'default',
       ('queue', 'manually_confirm', 'metadata', 'location',)),
    Lb('📥본문(파괴)', 'metadata', ('queue', 'completely', 'metadata', 'overwrite', )),
    Lb('📥위치', 'location', ('queue', 'manually_confirm', 'location', 'overwrite', )),
    Lb('⛳수합 완료', 'completely', ('success', )),
    Lb('⭕정보 없음', 'pass', ('success', )),
    Lb('👤직접 입력', 'fill_manually', ('success', )),
    Lb('👤결과 검정', 'manually_confirm', ('success', )),
    Lb('❓링크 찾기', 'no_meta_url', ('fail', )),
    Lb('❓위치 찾기', 'no_location', ('fail', )),
]
STATUS_COLUMN = Cl(key='🏁준비', alias='edit_status',
                   marked_values=_STATUS_MARKS)

READING_FRAME = PropertyFrame([
    Cl(key='📘유형', alias='media_type', ),
    Cl(key='📔도서류', alias='is_book'),
    STATUS_COLUMN,
    Cl(key='📚제목', aliases=['docx_name', 'title']),
    Cl(key='📚원제(검색용)', alias='true_name'),
    Cl(key='📚부제', alias='subname'),
    Cl(key='📚링크', alias='url'),
    Cl(key='📚만든이', alias='author'),
    Cl(key='📚만든곳', alias='publisher'),
    Cl(key='📚N(쪽)', alias='volume'),
    Cl(key='📚표지', alias='cover_image'),
    Cl(key='📚위치', alias='location'),
    Cl(key='📚대출중', alias='not_available'),
    Cl(key='📦지정', alias='link_to_contents'),
])
