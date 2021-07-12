from notion_py.interface.structure import Requestor, retry


class DatabaseRetrieve(Requestor):
    def __init__(self, database_id: str):
        self.database_id = database_id

    def apply(self):
        return {'database_id': self.database_id}

    @retry
    def execute(self):
        return self.notion.databases.retrieve(**self.apply())


class PageRetrieve(Requestor):
    def __init__(self, page_id: str):
        self.page_id = page_id

    def apply(self):
        return {'page_id': self.page_id}

    @retry
    def execute(self):
        return self.notion.pages.retrieve(**self.apply())


class BlockChildrenList(Requestor):
    def __init__(self, block_id: str):
        self.block_id = block_id

    def apply(self):
        return {'block_id': self.block_id}

    @retry
    def execute(self):
        return self.notion.blocks.children.list(**self.apply())
