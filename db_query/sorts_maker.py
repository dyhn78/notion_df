class QuerySorts:
    def __init__(self, order=None):
        self.orders = []
        if order:
            self.append(order)

    def append(self, order):
        self.orders.append(order)

    def appendleft(self, order):
        self.orders.insert(0, order)

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
