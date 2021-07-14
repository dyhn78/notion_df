from typing import Callable, Any


def try_twice(function: Callable[[str], Any]):
    def wrapper(strings: tuple[str, str]):
        first_str, second_str = strings
        has_true_name = second_str and (second_str != first_str)
        result = function(first_str)
        if not result and has_true_name:
            result = function(second_str)
        return result
    return wrapper


def try_twice_and_return_default_value(function: Callable[[Any, str], Any]):
    def wrapper(self, strings: tuple[str, str]):
        first_str, second_str = strings
        has_true_name = second_str and (second_str != first_str)
        result = function(self, first_str)
        if not result and has_true_name:
            result = function(self, second_str)
        if not result:
            return self.default_value
        return result
    return wrapper
