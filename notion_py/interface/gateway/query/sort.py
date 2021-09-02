from notion_py.interface.struct import ListStash


class QuerySort(ListStash):
    def unpack(self) -> dict:
        return {'sorts': self._unpack()}

    def append_ascending(self, prop_name):
        self._subdicts.append(self.__sort(prop_name, 'ascending'))

    def append_descending(self, prop_name):
        self._subdicts.append(self.__sort(prop_name, 'descending'))

    def appendleft_ascending(self, prop_name):
        self._subdicts.insert(0, self.__sort(prop_name, 'ascending'))

    def appendleft_descending(self, prop_name):
        self._subdicts.insert(0, self.__sort(prop_name, 'descending'))

    @staticmethod
    def __sort(prop_name, direction):
        return {'property': prop_name,
                'direction': direction}