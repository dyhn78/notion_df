class QuerySort:
    @classmethod
    def make_ascending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'ascending')

    @classmethod
    def make_descending_sort(cls, prop_name):
        return cls.__make_sort(prop_name, 'descending')

    @staticmethod
    def __make_sort(prop_name, direction):
        return {
            'property': prop_name,
            'direction': direction,
        }
