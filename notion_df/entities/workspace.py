import os

from notion_df.entities.core import Entity
from notion_df.utils.misc import get_num_iterator

_num_iterator = get_num_iterator()

NOTION_API_KEY = os.getenv('NOTION_API_KEY')


class Workspace(Entity):
    def __init__(self):
        super().__init__()
        self._pk = next(_num_iterator)

    @property
    def pk(self) -> str:
        return f"workspace__{self._pk}"
