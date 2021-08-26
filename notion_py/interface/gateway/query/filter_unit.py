from abc import abstractmethod, ABCMeta
from pprint import pprint

from notion_py.interface.struct import ValueCarrier


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


class PlainFilter(QueryFilter):
    def __init__(self, plain_filter: dict):
        self._value = plain_filter

    def __bool__(self):
        return bool(self._value)

    @property
    def nesting(self):
        return 0

    def unpack(self):
        return self._value


class CompoundFilter(QueryFilter, metaclass=ABCMeta):
    def __init__(self, elements: list[QueryFilter]):
        self.elements = []
        self._nesting = 0
        self.extend(elements)

    def __iter__(self):
        return self.elements

    def __bool__(self):
        return bool(self.elements)

    @property
    def nesting(self):
        return self._nesting

    def append(self, element: QueryFilter):
        return self.extend([element])

    def extend(self, elements: list[QueryFilter]):
        homos = [e for e in elements if type(e) == type(self)]
        heteros = [e for e in elements if type(e) != type(self)]
        for e in homos:
            assert isinstance(e, CompoundFilter)
            self.elements.extend(e.elements)
            self._nesting = max(self._nesting, e.nesting)
        for e in heteros:
            self.elements.append(e)
            self._nesting = max(self._nesting, 1 + e.nesting)
        if self.nesting > 2:
            # TODO: AssertionError 대신 커스텀 에러클래스 정의
            pprint(self.unpack())
            raise ValueError('Nesting greater than 2!')


class AndFilter(CompoundFilter):
    def unpack(self):
        return {'and': list(e.unpack() for e in self.elements)}


class OrFilter(CompoundFilter):
    def unpack(self):
        return {'or': list(e.unpack() for e in self.elements)}
