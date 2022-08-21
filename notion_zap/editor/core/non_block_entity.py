from notion_zap.editor.core.entity import BaseEntity
from notion_zap.editor.core.utils import get_num_iterator

_num_iterator = get_num_iterator()


class Workspace(BaseEntity):
    def __init__(self):
        self._pk = next(_num_iterator)

    @property
    def pk(self) -> str:
        return f"workspace__{self._pk}"
