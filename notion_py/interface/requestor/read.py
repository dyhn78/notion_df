from .requestor_struct import PointRequestor, print_response_error, LongRequestor
from ..editor.editor_struct import PointEditor
from ..utility import stopwatch


class RetrieveDatabase(PointRequestor):
    def __init__(self, editor: PointEditor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(database_id=self.target_id)

    @print_response_error
    def execute(self):
        return self.notion.databases.retrieve(**self.unpack())

    def print_comments(self):
        if self.target_name:
            form = ['retrieve_database', f"< {self.target_name} >",
                    '\n\t', self.target_id]
        else:
            form = ['retrieve_database', self.target_id]
        comments = ' '.join(form)
        stopwatch(comments)


class RetrievePage(PointRequestor):
    def __init__(self, editor: PointEditor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(page_id=self.target_id)

    @print_response_error
    def execute(self):
        res = self.notion.pages.retrieve(**self.unpack())
        self.print_comments()
        return res

    def print_comments(self):
        if self.target_name:
            form = ['retrieve_page', f"< {self.target_name} >",
                    '\n\t', self.target_id]
        else:
            form = ['retrieve_page', self.target_id]
        comments = ' '.join(form)
        stopwatch(comments)


class RetrieveBlock(PointRequestor):
    def __init__(self, editor: PointEditor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self):
        return dict(block_id=self.target_id)

    @print_response_error
    def execute(self):
        res = self.notion.blocks.retrieve(**self.unpack())
        self.print_comments()
        return res

    def print_comments(self):
        if self.target_name:
            form = ['retrieve_block', f"< {self.target_name} >",
                    '\n\t', self.target_id]
        else:
            form = ['retrieve_block', self.target_id]
        comments = ' '.join(form)
        stopwatch(comments)


class GetBlockChildren(LongRequestor):
    def __init__(self, editor: PointEditor):
        super().__init__(editor)

    def __bool__(self):
        return bool(self.target_id)

    def unpack(self, page_size=None, start_cursor=None):
        args = dict(block_id=self.target_id,
                    page_size=(page_size if page_size else self.MAX_PAGE_SIZE))
        if start_cursor:
            args.update(start_cursor=start_cursor)
        return args

    def execute(self, request_size=0):
        res = self._execute_all(request_size, False)
        self.print_comments()
        return res

    @print_response_error
    def _execute_each(self, request_size, start_cursor=None):
        return self.notion.blocks.children.list(
            **self.unpack(page_size=request_size, start_cursor=start_cursor)
        )

    def print_comments(self):
        if self.target_name:
            form = ['fetch_children', f"< {self.target_name} >",
                    '\n\t', self.target_id]
        else:
            form = ['fetch_children', self.target_id]
        comments = ' '.join(form)
        stopwatch(comments)
