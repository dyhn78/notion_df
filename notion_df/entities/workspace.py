import os

from notion_df.utils.misc import get_num_iterator

_num_iterator = get_num_iterator()


class Workspace:
    def __init__(self, token: str = os.getenv('NOTION_TOKEN')):
        super().__init__()
        self.token = token
        self._pk = next(_num_iterator)

    @property
    def pk(self) -> str:
        return f"workspace__{self._pk}"
