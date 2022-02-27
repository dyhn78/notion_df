def duplicate_tag(chars):
    chars.update(char.replace('<', '</')
                 for char in chars.copy())
    chars.update(char.replace('>', '/>') for char in chars.copy())
    chars.update(char.upper() for char in chars.copy())
    return chars


CHARS_TO_DELETE = duplicate_tag({'<b>', '<strong>', r'\t', '__'})
CHARS_TO_SPLIT = duplicate_tag({'<br/>', '</br>', '<br>', '\n', '|'})
CHARS_TO_STRIP = duplicate_tag({'"', "'", ' ', '·'})
CHARS_TO_LSTRIP = duplicate_tag({'?'})
MAX_LINE_LENGTH = 2000  # due to Notion API


def parse_contents(contents_html: str):
    # filter
    filtered = contents_html
    for char in CHARS_TO_DELETE:
        contents_html = contents_html.replace(char, ' ')
        filtered = filtered.strip()

    splited = [filtered]
    for char in CHARS_TO_SPLIT:
        prev = splited
        splited = []
        for line in prev:
            splited.extend(line.split(char))

    striped = []
    for line in splited:
        for char in CHARS_TO_STRIP:
            line = line.strip(char)
        for char in CHARS_TO_LSTRIP:
            line = line.lstrip(char)
        line = line.replace(" ", " ")
        if not line.replace(' ', ''):
            continue  # skip totally-blank lines
        striped.append(line)

    sliced = []
    for line in striped:
        line_frags = [line[i:i + MAX_LINE_LENGTH] for i in
                      range(0, len(line), MAX_LINE_LENGTH)]
        sliced.extend(line_frags)
    return sliced


if __name__ == '__main__':
    html = "목차<br/><br/>이야기를 열며 <br/>" \
           "<br/> 제1강 '카페인 없는 커피' 가게에 오신 것을 " \
           "환영합니다 <br/> 이데올로기의 욕망, 또는 욕망의 이데올로기 <br/>" \
           "<br/> 제2강 프랜시스 후쿠야마 이후 <br/>" \
           "또는 자유민주주의의 종말에 관하여 <br/>\
           <br/> 제3강 새로운 열림의 공간을 향하여 <br/> " \
           "다시, '시장근본주의 너머'의 정치를 상상한다는 것" \
           "<br/><br/> 제4강 강연이 끝난 후 " \
           "<br/> 나와 세계를 바꾸는 '다른 정치'의 조건들 " \
           "<br/><br/> 강연자와 옮긴이 소개"

    from pprint import pprint
    pprint(parse_contents(html))
