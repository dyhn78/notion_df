from typing import Callable, Any

import emoji


def try_func_twice(function: Callable[[str], Any]):
    def wrapper(strings: tuple[str, str]):
        first_str, second_str = strings
        has_true_name = second_str and (second_str != first_str)
        result = function(first_str)
        if not result and has_true_name:
            result = function(second_str)
        return result

    return wrapper


def try_method_twice(function: Callable[[Any, str], Any]):
    def wrapper(self, strings: tuple[str, str]):
        first_str, second_str = strings
        has_true_name = second_str and (second_str != first_str)
        result = function(self, first_str)
        if not result and has_true_name:
            result = function(self, second_str)
        return result

    return wrapper


def remove_emoji(text):
    return emoji.get_emoji_regexp().sub(u'', text)
