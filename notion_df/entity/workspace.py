from notion_df.core import Entity
from notion_df.util import get_num_iterator

_num_iterator = get_num_iterator()


class Workspace(Entity):
    def __init__(self):
        self._pk = next(_num_iterator)

    @property
    def pk(self) -> str:
        return f"workspace__{self._pk}"
