from notion_py.gateway.common import retry_request, GatewayRequestor, LongRequestor


class RetrieveDatabase(GatewayRequestor):
    def __init__(self, database_id: str):
        self.database_id = database_id

    def unpack(self):
        return {'database_id': self.database_id}

    @retry_request
    def execute(self):
        return self.notion.databases.retrieve(**self.unpack())


class RetrievePage(GatewayRequestor):
    def __init__(self, page_id: str):
        self.page_id = page_id

    def unpack(self):
        return {'page_id': self.page_id}

    @retry_request
    def execute(self):
        return self.notion.pages.retrieve(**self.unpack())


class GetBlockChildren(LongRequestor):
    def __init__(self, block_id: str):
        self.block_id = block_id

    def unpack(self):
        return {'block_id': self.block_id}

    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        args = dict(**self.unpack(),
                    page_size=(page_size if page_size else self.MAX_PAGE_SIZE))
        if start_cursor:
            args.update(start_cursor=start_cursor)
        return self.notion.blocks.children.list(**args)
