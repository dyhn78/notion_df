from typing import Optional


class PropertyFrame(dict):
    def __init__(self, values: Optional[dict] = None):
        if values is None:
            values = {}
        super().__init__({key: PropertyUnit(value) for key, value in values.items()})


class PropertyUnit:
    def __init__(self, values=None):
        if type(values) == tuple:
            prop_name, prop_value = values
        elif type(values) == str:
            prop_name = values
            prop_value = None
        else:
            raise AssertionError(f'Invalid PropertyUnit: {values}')
        self.name = prop_name
        self.value = prop_value