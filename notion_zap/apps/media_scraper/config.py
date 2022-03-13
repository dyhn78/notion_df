from notion_zap.cli.structs import PropertyColumn as Cl, PropertyFrame

STATUS_DEFAULT = ('queue', 'metadata', 'location', 'manually_confirm')
STATUSES = Cl(key='🏁준비', tag='edit_status',
              labels={
                  STATUS_DEFAULT: '📥본문(비파괴)/위치',
                  ('queue', 'metadata', 'overwrite', 'completely'): '📥본문(파괴)',
                  ('queue', 'location', 'overwrite', 'manually_confirm'): '📥위치',
                  ('success', 'completely'): '⛳수합 완료',
                  ('success', 'pass'): '⭕정보 없음',
                  ('success', 'fill_manually'): '👤직접 입력',
                  ('success', 'manually_confirm'): '👤결과 검정',
                  ('fail', 'no_meta_url'): '❓링크 찾기',
                  ('fail', 'no_loc'): '❓위치 찾기', }, )
STATUS_REGULAR = [value for label, value in STATUSES.labels.items() if 'queue' in label]

READING_FRAME = PropertyFrame([
    Cl(key='📘유형', tag='media_type', ),
    Cl(key='📔도서류', tag='is_book'),
    STATUSES,
    Cl(key='📚제목', tags=['docx_name', 'title']),
    Cl(key='📚원제(검색용)', tag='true_name'),
    Cl(key='📚부제', tag='subname'),
    Cl(key='📚링크', tag='url'),
    Cl(key='📚만든이', tag='author'),
    Cl(key='📚만든곳', tag='publisher'),
    Cl(key='📚N(쪽)', tag='volume'),
    Cl(key='📚표지', tag='cover_image'),
    Cl(key='📚위치', tag='location'),
    Cl(key='📚대출중', tag='not_available'),
    Cl(key='📦이동', tag='link_to_contents'),
])
