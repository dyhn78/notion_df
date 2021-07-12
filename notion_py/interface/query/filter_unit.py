from abc import ABC, abstractmethod
from pprint import pprint


class QueryFilter(ABC):
    """참고로, nesting 기준이 Notion 앱에서보다 더 강하다.
    예를 들어 any('contains', ['1', 'A', '@'] 형식으로 필터를 구성할 경우
    Notion 앱에서는 nesting == 0이지만, API 상에서는 1로 판정한다."""
    @abstractmethod
    def apply(self):
        pass

    @property
    @abstractmethod
    def nesting(self):
        pass

    def __and__(self, other):
        """filter1 & filter2 형식으로 사용할 수 있다."""
        return AndFilter(self, other)

    def __or__(self, other):
        """filter1 | filter2 형식으로 사용할 수 있다."""
        return OrFilter(self, other)


class PlainFilter(QueryFilter):
    def __init__(self, plain_filter: dict):
        self.value = plain_filter

    def apply(self):
        return self.value

    @property
    def nesting(self):
        return 0


class CompoundFilter(QueryFilter):
    def __init__(self, *elements):
        homos = []
        heteros = []
        for e in elements:
            if type(e) == type(self):
                homos.append(e)
            else:
                heteros.append(e)

        self._nesting = 0
        if homos:
            self._nesting = max(e.nesting for e in homos)
        if heteros:
            self._nesting = max(self._nesting, 1 + max(e.nesting for e in heteros))
        if self.nesting > 2:
            # TODO: AssertionError 대신 커스텀 에러클래스 정의
            print('Nested greater than 2!')
            pprint(self.apply())
            raise AssertionError

        self.elements = heteros
        for e in homos:
            self.elements.extend(e.elements)

    @abstractmethod
    def apply(self):
        pass

    @property
    def nesting(self):
        return self._nesting


class AndFilter(CompoundFilter):
    def apply(self):
        return {'and': list(e.apply() for e in self.elements)}


class OrFilter(CompoundFilter):
    def apply(self):
        return {'or': list(e.apply() for e in self.elements)}