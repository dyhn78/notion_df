from interface.requests.structures import ListStash


class QuerySort(ListStash):
    def apply(self) -> dict:
        return {'sorts': self._unpack()}

    def append_ascending(self, prop_name):
        self.stash(self.__sort(prop_name, 'ascending'))

    def append_descending(self, prop_name):
        self.stash(self.__sort(prop_name, 'descending'))

    def appendleft_ascending(self, prop_name):
        self.stashleft(self.__sort(prop_name, 'ascending'))

    def appendleft_descending(self, prop_name):
        self.stashleft(self.__sort(prop_name, 'descending'))

    @staticmethod
    def __sort(prop_name, direction):
        return {'property': prop_name,
                'direction': direction}
