def parse_rich_texts(rich_texts):
    plain_text = ''.join([rich_text_object['plain_text']
                          for rich_text_object in rich_texts])
    rich_text = []
    for rich_text_object in rich_texts:
        rich_text.append(
            {key: rich_text_object[key]
             for key in ['type', 'text', 'mention', 'equation']
             if key in rich_text_object}
        )
    return plain_text, rich_text
