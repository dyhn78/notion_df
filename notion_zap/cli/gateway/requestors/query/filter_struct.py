from abc import abstractmethod, ABCMeta
from pprint import pprint

from notion_zap.cli.struct.base_logic import ValueCarrier


class QueryFilter(ValueCarrier):
    """참고로, nesting 기준이 Notion 앱에서보다 더 강하다.
    예를 들어 any('contains', ['1', 'A', '@'] 형식으로 필터를 구성할 경우
    Notion 앱에서는 nesting == 0이지만, API 상에서는 1로 판정한다."""

    @property
    @abstractmethod
    def nesting(self):
        pass

    def __and__(self, other):
        """filter1 & filter2 형식으로 사용할 수 있다."""
        return AndFilter([self, other])

    def __or__(self, other):
        """filter1 | filter2 형식으로 사용할 수 있다."""
        return OrFilter([self, other])


class EmptyFilter(QueryFilter):
    def __bool__(self):
        return False

    @property
    def nesting(self):
        return 0

    def encode(self):
        return {}


class PlainFilter(QueryFilter):
    def __init__(self, plain_filter: dict):
        self._value = plain_filter

    def __bool__(self):
        return bool(self._value)

    @property
    def nesting(self):
        return 0

    def encode(self):
        return self._value


class CompoundFilter(QueryFilter, metaclass=ABCMeta):
    def __init__(self, elements: list[QueryFilter]):
        self._nesting = 0
        self.elements: list[QueryFilter] = []
        self.extend(elements)

    @property
    def nesting(self):
        return self._nesting

    def __iter__(self):
        return iter(self.elements)

    def __bool__(self):
        return bool(self.elements)

    def append(self, ft: QueryFilter):
        self._append(ft)
        self._check_nesting()

    def extend(self, fts: list[QueryFilter]):
        for ft in fts:
            self._append(ft)
        self._check_nesting()

    def _append(self, ft: QueryFilter):
        if not isinstance(ft, QueryFilter):
            raise TypeError(ft)
        if isinstance(ft, EmptyFilter):
            return
        if type(ft) == type(self):
            assert isinstance(ft, CompoundFilter)
            self.elements.extend(ft.elements)
            self._nesting = max(self._nesting, ft.nesting)
        else:
            self.elements.append(ft)
            self._nesting = max(self._nesting, 1 + ft.nesting)

    def _check_nesting(self):
        if self.nesting > 2:
            # TODO: AssertionError 대신 커스텀 에러클래스 정의
            print("following CompoundFilter has nesting > 2 ::")
            self.preview()
            raise ValueError(self.encode())


class AndFilter(CompoundFilter):
    def encode(self):
        return {'and': list(e.encode() for e in self.elements)}


class OrFilter(CompoundFilter):
    def encode(self):
        return {'or': list(e.encode() for e in self.elements)}
