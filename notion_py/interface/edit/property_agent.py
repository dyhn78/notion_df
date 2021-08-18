from notion_py.gateway.write.property.unit import \
    BasicPageTitleWriter


class BasicPropertyAgent:
    @classmethod
    def rich_title(cls):
        return BasicPageTitleWriter('title')

    @classmethod
    def title(cls, value: str):
        return cls.rich_title().write_text(value)
