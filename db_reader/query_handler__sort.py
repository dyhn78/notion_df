class QuerySort:
    def __init__(self):
        self.apply = []

    def clear(self):
        self.apply = []

    def append_ascending(self, prop_name):
        self.apply.append(self.__make_ascending_sort(prop_name))

    def append_descending(self, prop_name):
        self.apply.append(self.__make_descending_sort(prop_name))

    def appendleft_ascending(self, prop_name):
        self.apply.insert(0, self.__make_ascending_sort(prop_name))

    def appendleft_descending(self, prop_name):
        self.apply.insert(0, self.__make_descending_sort(prop_name))

    @classmethod
    def __make_ascending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'ascending')

    @classmethod
    def __make_descending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'descending')

    @staticmethod
    def __make_sort(prop_name, direction):
        sort = {
            'property': prop_name,
            'direction': direction,
        }
        return sort
