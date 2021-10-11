from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Union, Optional

from notion_py.interface.struct import Editor, Requestor
from notion_py.interface.utility import page_id_to_url


class PointEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Union[PointEditor, Editor]):
        self.caller = caller
        super().__init__(caller.root_editor)

    @property
    def master(self) -> MasterEditor:
        return self.caller.master

    @property
    def parent(self) -> MasterEditor:
        return self.master.caller.master

    @property
    def master_id(self) -> str:
        return self.master.master_id

    @master_id.setter
    def master_id(self, value: str):
        self.master.master_id = value

    @property
    def parent_id(self) -> str:
        return self.parent.master_id

    @parent_id.setter
    def parent_id(self, value: str):
        self.parent.master_id = value

    @property
    def master_url(self):
        return page_id_to_url(self.master_id)

    @property
    def archived(self):
        return self.master.archived

    @archived.setter
    def archived(self, value: bool):
        self.master.archived = value

    @property
    def yet_not_created(self):
        return self.master.yet_not_created

    @yet_not_created.setter
    def yet_not_created(self, value: bool):
        self.master.yet_not_created = value


class MasterEditor(PointEditor):
    def __init__(self, caller: Union[PointEditor, Editor], master_id: str):
        super().__init__(caller)
        self.agents: dict[str, Union[PointEditor]] = {}
        self.master_id = master_id
        self._archived = False
        self._yet_not_created = False

        self.is_supported_type = False
        self.can_have_children = False
        self.has_children = False

    def __bool__(self):
        return any(agent for agent in self.agents.values())

    @property
    def yet_not_created(self):
        return self._yet_not_created

    @yet_not_created.setter
    def yet_not_created(self, value: bool):
        if value:
            assert not self.master_id
        self._yet_not_created = value

    @property
    def master(self):
        return self

    @property
    @abstractmethod
    def master_name(self):
        pass

    @property
    def master_id(self):
        return self._master_id

    @master_id.setter
    def master_id(self, value):
        self._master_id = value

    @property
    def parent_id(self):
        try:
            return self.parent.master_id
        except AttributeError:
            if self.master_url:
                message = f'cannot find parent_id at: {self.master_url}'
            else:
                message = (f"ERROR: provide master_id or parent_id for this block;\n"
                           f"editor info:\n"
                           f"{self.preview()}")
            raise AttributeError(message)

    @property
    def archived(self):
        return self._archived

    @archived.setter
    def archived(self, value: bool):
        self._archived = value

    def set_overwrite_option(self, option: bool):
        for requestor in self.agents.values():
            if hasattr(requestor, 'set_overwrite_option'):
                requestor.set_overwrite_option(option)

    @abstractmethod
    def preview(self):
        return {key: value.preview() for key, value in self.agents.items()}

    @abstractmethod
    def execute(self):
        return {key: value.execute() for key, value in self.agents.items()}

    @abstractmethod
    def fully_read(self):
        pass

    @abstractmethod
    def fully_read_rich(self):
        pass


class BridgeEditor(PointEditor, metaclass=ABCMeta):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.values: list[MasterEditor] = []

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any([child for child in self.values])

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def preview(self):
        return [child.preview() for child in self.values]

    def execute(self):
        return [child.execute() for child in self.values]


class GroundEditor(PointEditor, metaclass=ABCMeta):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.gateway: Optional[Requestor] = None
        self.enable_overwrite = True

    def __bool__(self):
        return bool(self.gateway)

    def set_overwrite_option(self, option: bool):
        self.enable_overwrite = option

    def preview(self):
        return self.gateway.unpack() if self.gateway else {}

    def execute(self):
        return self.gateway.execute() if self.gateway else {}


"""
from itertools import chain
from typing import ValuesView, Mapping

class AbstractMasterEditor(Executable):
    def __init__(self, master_id: str):
        self.master_id = master_id
        self.set_overwrite_option(True)

    @abstractmethod
    def set_overwrite_option(self, option: bool):
        pass

class EditorComponentStash(dict):
    def __init__(self, caller: EditorControl):
        super().__init__()
        self.caller = caller

    def values(self) -> ValuesView[EditorComponent]:
        return super().values()

    def update(self, __m: Mapping[str, EditorComponent],
               **kwargs: dict[str, EditorComponent]):
        super().update(__m, **kwargs)
        for key, value in chain(__m, kwargs):
            setattr(self.caller, key, value)


class StackEditor(AbstractMainEditor):
    def __init__(self, master_id: str):
        super().__init__(master_id)
        self.elements: list[MainEditor] = []

    def __iter__(self) -> list[MainEditor]:
        return self.elements

    def set_overwrite_option(self, option: bool):
        for child in self:
            child.set_overwrite_option(option)

    def unpack(self):
        return [child.unpack() for child in self]

    def execute(self):
        return [child.execute() for child in self]
"""
