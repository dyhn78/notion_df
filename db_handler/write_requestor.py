from db_handler.write_requestor__base import PageWriteRequestor, DatabaseWriteRequestor as DBWriteRequestor


class PageCreateRequestor(PageWriteRequestor):
    parent_id_type = 'page_id'

    def __init__(self, notion, parent_id: str):
        super().__init__(notion)
        self.parent_id = parent_id

    @property
    def apply(self):
        return {
            'parent': {self.parent_id_type: self.parent_id},
            'properties': self.props
        }

    def execute(self):
        return self.notion.pages.create(**self.apply)


class DatabaseCreateRequestor(PageCreateRequestor, DBWriteRequestor):
    parent_id_type = 'database_id'

    def __init__(self, notion, parent_id: str, database_parser=None):
        DBWriteRequestor.__init__(self, notion, database_parser)
        self.parent_id = parent_id


class PageUpdateRequestor(PageWriteRequestor):
    def __init__(self, notion, page_id: str):
        super().__init__(notion)
        self.page_id = page_id

    @property
    def apply(self):
        return {
            'page_id': self.page_id,
            'properties': self.props
        }

    def execute(self):
        return self.notion.pages.update(**self.apply)


class DatabaseUpdateRequestor(PageUpdateRequestor, DBWriteRequestor):
    def __init__(self, notion, page_id: str, database_parser=None):
        DBWriteRequestor.__init__(self, notion, database_parser)
        self.page_id = page_id
