from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Final, Generic, Hashable, Union, Optional, final, TypeVar, overload, \
    Literal, Any
from uuid import UUID

from typing_extensions import Self

from notion_df.core.contents import ContentsT, Contents
from notion_df.util.misc import repr_object, undefined

namespace: Final[dict[tuple[type[Entity], UUID], Entity]] = {}
ContentsT2 = TypeVar("ContentsT2", bound=Contents)


class Entity(Generic[ContentsT], Hashable, metaclass=ABCMeta):
    """The base class for blocks, users, and comments.

    There is only one instance with given subclass and id.
    You can identify two blocks directly `block_1 == block_2`,
    not need to `block_1.id == block_2.id`

    Use `default` attribute to hardcode some fixed data.
    """
    id: UUID
    _current: Optional[ContentsT] = None
    default: Optional[ContentsT] = None
    """custom local-only data."""

    @classmethod
    @abstractmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        pass

    def __new__(cls, id_or_url: Union[UUID, str],
                default: Optional[ContentsT] = None,
                *, current: Optional[Contents] = None):
        try:
            __id = cls._get_id(id_or_url)
            if (cls, __id) in namespace:
                return namespace[(cls, __id)]
            return super().__new__(cls)
        finally:
            del __id

    def __init__(self, id_or_url: Union[UUID, str],
                 default: Optional[ContentsT] = None,
                 *, current: Optional[Contents] = None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.id: Final[UUID] = self._get_id(id_or_url)
        namespace[(type(self), self.id)] = self
        self.current = current
        self.default = default

    def __del__(self):
        # TODO: consider using weakref instead.
        #  validate it with unit test which assert sys.getrefcount()
        del self.current
        del namespace[(type(self), self.id)]

    def __getnewargs__(self):  # required for pickling
        return self.id,

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Entity)
                and ((type(self), self.id) == (type(other), self.id)))

    def __repr__(self) -> str:
        return repr_object(self, id=self.id, parent=self._repr_parent())

    @property
    def current(self) -> Optional[ContentsT]:
        """the latest contents from the server."""
        return self._current

    @current.setter
    def current(self, contents: ContentsT) -> None:
        """set the contents as the more recent one between current one and new one."""
        if (self.current is None) or (contents.timestamp > self.current.timestamp):
            self._current = contents

    @current.deleter
    def current(self) -> None:
        self._current = None

    @overload
    def get(self, retrieve_if_empty: Literal[True] = True) -> ContentsT:
        ...

    @overload
    def get(self, retrieve_if_empty: Literal[False] = False) -> Optional[ContentsT]:
        ...

    @overload
    def get(self, cast: type[ContentsT2] = Contents,
            retrieve_if_empty: Literal[True] = True) -> ContentsT2:
        ...

    @overload
    def get(self, cast: type[ContentsT2] = Contents,
            retrieve_if_empty: Literal[False] = False) -> Optional[ContentsT2]:
        ...

    def get(self, cast: type[ContentsT2] = Contents,
            retrieve_if_empty: bool = True) -> Optional[ContentsT2]:
        """get the local contents, or retrieve."""
        # TODO: merge(self.current, self.default)
        contents = self.current if self.current is not None else self.default
        if contents is None:
            if not retrieve_if_empty:
                return None
            self.retrieve()
        return cast.from_base_class(contents)

    @abstractmethod
    def retrieve(self) -> Self:
        # TODO: raise EntityNotExistError(ValueError), with page_exists()
        pass

    @final
    def _repr_parent(self) -> Optional[str]:
        if self.current is None:
            return undefined
        elif self.current.parent is None:
            return 'workspace'
        else:  # TODO: fix that user and comments does not have parent
            return self.current.parent._repr_as_parent()

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)
