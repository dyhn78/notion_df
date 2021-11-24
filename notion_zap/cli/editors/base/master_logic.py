from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Union
import datetime as dt

from notion_zap.cli.utility import page_id_to_url
from .base import Editor


class BlockEditor(Editor, metaclass=ABCMeta):
    def __init__(self, caller: Union[BlockEditor, Editor]):
        self.caller = caller
        super().__init__(caller.root)

    @property
    def master(self) -> MasterEditor:
        return self.caller.master

    @property
    def block_id(self) -> str:
        return self.master.block_id

    @property
    def block_url(self):
        return page_id_to_url(self.block_id)

    @property
    def block_name(self) -> str:
        return self.master.block_name

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        return self.master.parent

    @property
    def parent_id(self) -> str:
        return self.master.parent_id

    @property
    def archived(self):
        return self.master.archived

    @property
    def yet_not_created(self):
        return self.master.yet_not_created
    #
    # @yet_not_created.setter
    # def yet_not_created(self, value: bool):
    #     self.master.yet_not_created = value


class MasterEditor(BlockEditor):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        """implementations:
        1. declare payload, make it register to parent/root (.by_id, .by_title):
            this allows to search and read specific page from the collection.
        2. attach self to pagelist (.update.blocks, .create.blocks):
            this determine the order of saving process of the collection.
        """

    @property
    @abstractmethod
    def is_supported_type(self) -> bool:
        pass

    @property
    @abstractmethod
    def payload(self) -> PayloadEditor:
        pass

    @property
    def created_time(self):
        return self.payload.created_time

    @property
    def last_edited_time(self):
        return self.payload.last_edited_time

    @property
    def archived(self):
        return self.payload.archived

    @property
    def has_children(self) -> bool:
        return self.payload.has_children

    @property
    def can_have_children(self) -> bool:
        return self.payload.can_have_children

    @property
    def yet_not_created(self):
        return self.payload.yet_not_created

    @property
    def master(self):
        return self

    @property
    def block_id(self):
        return self.payload.block_id

    @property
    @abstractmethod
    def block_name(self):
        pass

    @property
    def parent(self):
        """if the master is directly called by RootEditor, this will return None."""
        if self.caller == self.root:
            return None
        parent = self.caller.master
        from ..common.with_children import ChildrenBearer
        assert isinstance(parent, ChildrenBearer)
        return parent

    @property
    def parent_id(self):
        from ..common.with_children import ChildrenBearer
        parent = self.parent
        try:
            assert isinstance(parent, ChildrenBearer)
            return self.parent.block_id
        except AssertionError:
            from notion_zap.cli.editors.editor_exceptions import NoParentFoundError
            raise NoParentFoundError(self.master)

    @property
    def entry_ancestor(self):
        if self.yet_not_created:
            return self.parent.entry_ancestor
        return self

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
            have to refer to self.block_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """


class PayloadEditor(BlockEditor, metaclass=ABCMeta):
    def __init__(self, caller: Union[BlockEditor, Editor], block_id: str):
        super().__init__(caller)
        self.__block_id = ''
        self._set_block_id(block_id)
        self._archived = None
        self._created_time = None
        self._last_edited_time = None

        self._has_children = None
        self._can_have_children = None

    @property
    def created_time(self) -> dt.datetime:
        return self._created_time

    @property
    def last_edited_time(self) -> dt.datetime:
        return self._last_edited_time

    @property
    def archived(self):
        return False if self._archived is None else self._archived

    @property
    def yet_not_created(self):
        return self.block_id == ''

    @property
    def has_children(self):
        return self.can_have_children \
            if self._has_children is None else self._has_children

    @property
    def can_have_children(self):
        return True \
            if self._can_have_children is None else self._can_have_children

    @property
    def block_id(self) -> str:
        return self.__block_id

    def _set_block_id(self, value):
        self._unregister_id()
        self.__block_id = value
        self._register_id()

    def unregister_all(self):
        self._unregister_id()

    def _register_id(self):
        if self.block_id == '':
            return
        # register to root
        register_point = self.root.by_id
        register_point[self.block_id] = self.master
        # register to parent
        if self.parent is not None:
            register_point = self.parent.children.by_id
            register_point[self.block_id] = self.master

    def _unregister_id(self):
        if self.block_id == '':
            return
        # detach from root
        register_point = self.root.by_id
        register_point.pop(self.block_id)
        # detach from parent
        if self.parent is not None:
            register_point = self.parent.children.by_id
            register_point.pop(self.block_id)
