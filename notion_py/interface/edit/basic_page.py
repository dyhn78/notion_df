from .block import Block


class BasicPage(Block):
    def __init__(self, page_id: str):
        super().__init__(page_id)
        self.title = ''
        pass

    def unpack(self):
        pass

    def execute(self):
        pass

    def read_title(self):
        pass

    def read_rich_title(self):
        pass

    def write_title(self):
        pass

    def write_rich_title(self):
        pass
