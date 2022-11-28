from typing import Callable

# noinspection PyPackageRequirements
from googleapiclient.errors import HttpError

from .open_service import GcalManagerAbs


def print_response_error(func: Callable):
    def wrapper(self: GcalManagerAbs, **kwargs):
        try:
            response = func(self, **kwargs)
            return response
        except HttpError as api_response_error:
            print()
            print(f'Error occurred while executing {type(self).__name__} ::')
            self.preview()
            print()
            raise api_response_error

    return wrapper
