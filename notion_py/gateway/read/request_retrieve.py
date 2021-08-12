from ..structure import retry_request, Requestor, LongRequestor


class RetrieveDatabase(Requestor):
    def __init__(self, database_id: str):
        self.database_id = database_id

    def apply(self):
        return {'database_id': self.database_id}

    @retry_request
    def execute(self):
        return self.notion.databases.retrieve(**self.apply())


class RetrievePage(Requestor):
    def __init__(self, page_id: str):
        self.page_id = page_id

    def apply(self):
        return {'page_id': self.page_id}

    @retry_request
    def execute(self):
        return self.notion.pages.retrieve(**self.apply())


class RetrieveBlockChildren(LongRequestor):
    def __init__(self, block_id: str):
        self.block_id = block_id

    def apply(self):
        return {'block_id': self.block_id}

    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        page_size = {'page_size': (page_size if page_size else self.MAX_PAGE_SIZE)}
        start_cursor = {'start_cursor': start_cursor} if start_cursor else None
        args = self._merge_dict(self.apply(), start_cursor, page_size)
        return self.notion.blocks.children.list(**args)
