from interface.requests.structures import ListStash, PlainCarrier


class QuerySort(ListStash):
    def apply(self) -> dict:
        return {'sorts': self.stash()}

    def append_ascending(self, prop_name):
        self.append_to_liststash(self.ascending_sort(prop_name))

    def append_descending(self, prop_name):
        self.append_to_liststash(self.descending_sort(prop_name))

    def appendleft_ascending(self, prop_name):
        self.appendleft_to_liststash(self.ascending_sort(prop_name))

    def appendleft_descending(self, prop_name):
        self.appendleft_to_liststash(self.descending_sort(prop_name))

    @classmethod
    def ascending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'ascending')

    @classmethod
    def descending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'descending')

    @staticmethod
    def __make_sort(prop_name, direction):
        return PlainCarrier({
            'property': prop_name,
            'direction': direction,
        })
