from abc import ABCMeta
from typing import Optional

from notion_py.gateway.common import Requestor


class EditorMaster(Requestor):
    def __init__(self, target_id: str):
        self.components: dict[str, EditorComponent] = {}
        self.target_id = target_id
        self.set_overwrite_option(True)

    def set_overwrite_option(self, option: bool):
        for requestor in self.components.values():
            requestor.apply_overwrite_option(option)

    def unpack(self):
        return {key: value.unpack() for key, value in self.components}

    def execute(self):
        return {key: value.execute() for key, value in self.components}


class EditorComponent(Requestor, metaclass=ABCMeta):
    def __init__(self, caller: EditorMaster):
        self.agent: Optional[Requestor] = None
        self.caller = caller
        self.enable_overwrite = True

    def apply_overwrite_option(self, option: bool):
        self.enable_overwrite = option

    def unpack(self):
        return self.agent.unpack()

    def execute(self):
        return self.agent.execute()
