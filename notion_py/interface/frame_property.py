from typing import Optional


class PropertyFrame(dict):
    def __init__(self, values: Optional[dict] = None):
        super().__init__()
        if not values:
            return
        for key, value in values.items():
            self.update(key=PropertyUnit(value))


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
