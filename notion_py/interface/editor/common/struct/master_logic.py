from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Union

from notion_py.interface.utility import page_id_to_url
from .base import Editor


class PointEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Union[PointEditor, Editor]):
        self.caller = caller
        super().__init__(caller.root)

    @property
    def master(self) -> MasterEditor:
        return self.caller.master

    @property
    def master_id(self) -> str:
        return self.master.master_id

    @master_id.setter
    def master_id(self, value: str):
        self.master.master_id = value

    @property
    def master_url(self):
        return page_id_to_url(self.master_id)

    @property
    def master_name(self) -> str:
        return self.master.master_name

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        return self.master.parent

    @property
    def parent_id(self) -> str:
        return self.master.parent_id

    @parent_id.setter
    def parent_id(self, value: str):
        self.master.parent_id = value

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
    def __init__(self, caller: Editor, master_id: str):
        super().__init__(caller)
        self._master_id = ''
        self.master_id = master_id

        self._archived = False
        self._yet_not_created = False

    @property
    @abstractmethod
    def payload(self):
        pass

    @property
    def is_supported_type(self) -> bool:
        return False

    @property
    def can_have_children(self) -> bool:
        return False

    @property
    def has_children(self) -> bool:
        return False

    @property
    def master(self):
        return self

    @property
    def master_id(self):
        return self._master_id

    @master_id.setter
    def master_id(self, value: str):
        old_value = self.master_id
        self._master_id = value

        # register to root
        register_point = self.root.by_id
        if old_value:
            register_point.pop(old_value)
        if value:
            register_point[value] = self

        # register to parent
        if self.parent is not None:
            register_point = self.parent.children.by_id
            if old_value:
                register_point.pop(old_value)
            if value:
                register_point[value] = self

    @property
    @abstractmethod
    def master_name(self):
        pass

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        if self.caller == self.root:
            return None
        parent = self.caller.master
        from ..with_children import ChildrenBearer
        assert isinstance(parent, ChildrenBearer)
        return parent

    @property
    def parent_id(self):
        # TODO  아래의 세터와 일관성 갖추기.
        if self.parent is not None:
            return self.parent.master_id
        else:
            if self.master_url:
                message = f'cannot find parent_id at: {self.master_url}'
            else:
                message = (f"ERROR: provide master_id or parent_id for this block;\n"
                           f"editor info:\n"
                           f"{self.save_info()}")
            raise AttributeError(message)

    @parent_id.setter
    def parent_id(self, value: str):
        if self.parent is not None:
            self.parent.master_id = value
        else:
            raise AttributeError('you tried setting uuid of root_editor!')

    @property
    def entry_ancestor(self):
        if self.yet_not_created:
            return self.parent.entry_ancestor
        return self

    @property
    def archived(self):
        return self._archived

    @property
    def yet_not_created(self):
        return self._yet_not_created

    @yet_not_created.setter
    def yet_not_created(self, value: bool):
        if value:
            assert not self.master_id
        self._yet_not_created = value

    @archived.setter
    def archived(self, value: bool):
        self._archived = value

    @abstractmethod
    def reads(self):
        pass

    @abstractmethod
    def reads_rich(self):
        pass

    @abstractmethod
    def save_info(self):
        """ example:
        {'contents': "unpack contents here",
         'children': "unpack children here"}
        """

    @abstractmethod
    def save(self):
        """
        1. since self.children go first than self.new_children,
            saving a multi-rank structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.tabular,
            have to refer to self.master_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """
