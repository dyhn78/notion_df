def parse_contents(contents_raw: str) -> list[str]:
    chars_to_delete = {'<b>', '<strong>', r'\t', '__'}
    chars_to_delete = duplicate_char_variations(chars_to_delete)
    for char_to_delete in chars_to_delete:
        contents_raw = contents_raw.replace(char_to_delete, '')
    filtered = [contents_raw.strip()]
    for char_to_split in ['<br/>', '</br>', '<br>', '\n']:
        splited = []
        for text_line in filtered:
            splited.extend(text_line.split(char_to_split))
        filtered = []
        for text_line in splited:
            for char_to_strip in ['"', "'", ' ', '·']:
                text_line = text_line.strip(char_to_strip)
            for char_to_lstrip in ['?']:
                text_line = text_line.lstrip(char_to_lstrip)
            text_line = text_line.replace("  ", " ")
            if not text_line.replace(' ', ''):
                continue
            filtered.append(text_line)
    return filtered


def duplicate_char_variations(chars: set[str]) -> set[str]:
    chars.update(char.replace('<', '</') for char in chars.copy())
    chars.update(char.replace('>', '/>') for char in chars.copy())
    chars.update(char.upper() for char in chars.copy())
    return chars
