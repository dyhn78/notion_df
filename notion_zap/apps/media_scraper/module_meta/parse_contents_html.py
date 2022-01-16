def duplicate_tag(chars: set[str]) -> set[str]:
    chars.update(char.replace('<', '</') for char in chars.copy())
    chars.update(char.replace('>', '/>') for char in chars.copy())
    chars.update(char.upper() for char in chars.copy())
    return chars


CHARS_TO_DELETE = duplicate_tag({'<b>', '<strong>', r'\t', '__'})
CHARS_TO_SPLIT = duplicate_tag({'<br/>', '</br>', '<br>', '\n', '|'})
CHARS_TO_STRIP = duplicate_tag({'"', "'", ' ', '·'})
CHARS_TO_LSTRIP = duplicate_tag({'?'})
MAX_LINE_LENGTH = 2000  # due to Notion API

def parse_contents(contents_raw: str) -> list[str]:
    # filter
    for char in CHARS_TO_DELETE:
        contents_raw = contents_raw.replace(char, '')
    filtered = [contents_raw.strip()]

    # split
    splited = []
    for char in CHARS_TO_SPLIT:
        for line in filtered:
            splited.extend(line.split(char))

    # strip
    striped = []
    for line in splited:
        for char in CHARS_TO_STRIP:
            line = line.strip(char)
        for char in CHARS_TO_LSTRIP:
            line = line.lstrip(char)
        line = line.replace("  ", " ")
        if not line.replace(' ', ''):
            continue  # skip totally-blank lines
        sliced = [line[i:i + MAX_LINE_LENGTH]
                  for i in range(0, len(line), MAX_LINE_LENGTH)]
        for line_frag in sliced:
            striped.append(line_frag)

    return striped
