from notion_py.interface.struct import Gateway, retry_request, LongGateway, Editor


class RetrieveDatabase(Gateway):
    def __init__(self, editor: Editor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(database_id=self.target_id)

    @retry_request
    def execute(self):
        return self.notion.databases.retrieve(**self.unpack())


class RetrievePage(Gateway):
    def __init__(self, editor: Editor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(page_id=self.target_id)

    @retry_request
    def execute(self):
        return self.notion.pages.retrieve(**self.unpack())


class RetrieveBlock(Gateway):
    def __init__(self, editor: Editor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(block_id=self.target_id)

    @retry_request
    def execute(self):
        return self.notion.blocks.retrieve(**self.unpack())


class GetBlockChildren(LongGateway):
    def __init__(self, editor: Editor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self, page_size=None, start_cursor=None):
        args = dict(block_id=self.target_id,
                    page_size=(page_size if page_size else self.MAX_PAGE_SIZE))
        if start_cursor:
            args.update(start_cursor=start_cursor)
        return args

    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        return self.notion.blocks.children.list(
            **self.unpack(page_size=page_size, start_cursor=start_cursor)
        )
