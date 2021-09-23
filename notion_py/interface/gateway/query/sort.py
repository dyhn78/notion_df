class QuerySort:
    def __init__(self):
        self._list_stash = []

    def unpack(self) -> dict:
        return {'sorts': self._list_stash}

    def append_ascending(self, prop_name):
        self._list_stash.append(self._wrap_unit(prop_name, 'ascending'))

    def append_descending(self, prop_name):
        self._list_stash.append(self._wrap_unit(prop_name, 'descending'))

    def appendleft_ascending(self, prop_name):
        self._list_stash.insert(0, self._wrap_unit(prop_name, 'ascending'))

    def appendleft_descending(self, prop_name):
        self._list_stash.insert(0, self._wrap_unit(prop_name, 'descending'))

    @staticmethod
    def _wrap_unit(prop_name, direction):
        return {'property': prop_name,
                'direction': direction}
