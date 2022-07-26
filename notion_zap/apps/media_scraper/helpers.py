from typing import Callable, Any, Iterable

from emoji import demojize


def remove_emojis(data):
    demojize(data)


def enumerate_method(function: Callable[[Any, str], Any]):
    def wrapper(self, strings: Iterable[str]):
        visited = set()
        for string in strings:
            if string in visited:
                continue
            if lib_info := function(self, string):
                return lib_info
            visited.add(lib_info)

    return wrapper
