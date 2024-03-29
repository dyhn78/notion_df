from notion_zap.cli.utility import stopwatch
from .structs import Requestor, LongRequestor, print_response_error
from ...core.base import Component


class RetrieveDatabase(Requestor):
    def __init__(self, editor: Component):
        super().__init__(editor)

    def __bool__(self):
        return True

    def encode(self):
        return dict(database_id=self.target_id)

    @print_response_error
    def execute(self):
        return self.execute_silent()

    def execute_silent(self):
        return self.client.databases.retrieve(**self.encode())

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['retrieve_database', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['retrieve_database', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class RetrievePage(Requestor):
    def __init__(self, editor: Component):
        super().__init__(editor)

    def __bool__(self):
        return True

    def encode(self):
        return dict(page_id=self.target_id)

    @print_response_error
    def execute(self):
        return self.execute_silent()

    def execute_silent(self):
        res = self.client.pages.retrieve(**self.encode())
        return res

    def print_comments(self):
        super().print_comments()
        # TODO
        if self.target_name:
            form = ['retrieve_page', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['retrieve_page', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class RetrieveBlock(Requestor):
    def __init__(self, editor: Component):
        super().__init__(editor)

    def __bool__(self):
        return True

    def encode(self):
        return dict(block_id=self.target_id)

    @print_response_error
    def execute(self):
        res = self.client.blocks.retrieve(**self.encode())
        return res

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['retrieve_block', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['retrieve_block', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)


class GetBlockChildren(LongRequestor):
    def __init__(self, editor: Component):
        super().__init__(editor)

    def __bool__(self):
        return True

    def encode(self, page_size=None, start_cursor=None):
        if page_size is None:
            page_size = self.MAX_PAGE_SIZE
        args = dict(block_id=self.target_id,
                    page_size=page_size)
        if start_cursor is not None:
            args.update(start_cursor=start_cursor)
        return args

    def execute(self, request_size=0):
        res = self._execute_all(request_size, False)
        self.print_comments()
        return res

    @print_response_error
    def _execute_each(self, request_size, start_cursor=None):
        return self.client.blocks.children.list(
            **self.encode(request_size, start_cursor)
        )

    def print_comments(self):
        super().print_comments()
        if self.target_name:
            form = ['fetch_children', f"< {self.target_name} >",
                    '\n\t', self.target_url]
        else:
            form = ['fetch_children', self.target_url]
        comments = ' '.join(form)
        stopwatch(comments)
