def duplicate_tag(chars: set[str]) -> set[str]:
    chars.update(char.replace('<', '</') for char in chars.copy())
    chars.update(char.replace('>', '/>') for char in chars.copy())
    chars.update(char.upper() for char in chars.copy())
    return chars


CHARS_TO_DELETE = duplicate_tag({'<b>', '<strong>', r'\t', '__'})
CHARS_TO_SPLIT = duplicate_tag({'<br/>', '</br>', '<br>', '\n', '|'})
CHARS_TO_STRIP = duplicate_tag({'"', "'", ' ', '·'})
CHARS_TO_LSTRIP = duplicate_tag({'?'})


def parse_contents(contents_raw: str) -> list[str]:
    # filter
    for char in CHARS_TO_DELETE:
        contents_raw = contents_raw.replace(char, '')
    filtered = [contents_raw.strip()]

    # split
    splited = []
    for char in CHARS_TO_SPLIT:
        for text_line in filtered:
            splited.extend(text_line.split(char))

    # strip
    striped = []
    for text_line in splited:
        for char in CHARS_TO_STRIP:
            text_line = text_line.strip(char)
        for char in CHARS_TO_LSTRIP:
            text_line = text_line.lstrip(char)
        text_line = text_line.replace("  ", " ")
        if not text_line.replace(' ', ''):
            continue  # skip totally-blank lines
        striped.append(text_line)

    return striped
