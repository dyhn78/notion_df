from typing import Callable, Any, Iterable

import emoji


def remove_emoji(text):
    return emoji.get_emoji_regexp().sub(u'', text)


def enumerate_func(function: Callable[[str], Any]):
    def wrapper(strings: Iterable[str]):
        visited = set()
        for string in strings:
            if string in visited:
                continue
            if lib_info := function(string):
                return lib_info
            visited.add(lib_info)

    return wrapper


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
