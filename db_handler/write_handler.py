from db_handler.write__page_base import PageWriteHandler, DatabaseWriteHandler as DBWriteHandler


class PageCreateHandler(PageWriteHandler):
    """notion.pages.create(**self.apply)"""
    def __init__(self, parent_id: str, database_parser=None):
        super().__init__(database_parser)
        self.parent_id = parent_id
        self.parent_id_type = 'page_id'

    @property
    def apply(self):
        return {
            'parent': {'page_id': self.parent_id},
            'properties': self.properties
        }


class DatabaseCreateHandler(DBWriteHandler):
    """notion.pages.create(**self.apply)"""
    def __init__(self, parent_id: str, database_parser=None):
        super().__init__(database_parser)
        self.parent_id = parent_id

    @property
    def apply(self):
        return {
            'parent': {'database_id': self.parent_id},
            'properties': self.properties
        }


class PageUpdateHandler(PageWriteHandler):
    """notion.pages.update(**self.apply)"""
    def __init__(self, page_id: str, database_parser=None):
        super().__init__(database_parser)
        self.page_id = page_id

    @property
    def apply(self):
        return {
            'page_id': self.page_id,
            'properties': self.properties
        }


class DatabaseUpdateHandler(DBWriteHandler):
    def __init__(self, page_id: str, database_parser=None):
        super().__init__(database_parser)
        self.page_id = page_id

    @property
    def apply(self):
        return {
            'page_id': self.page_id,
            'properties': self.properties
        }
