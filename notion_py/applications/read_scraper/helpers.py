from typing import Callable, Any


def try_twice(function: Callable[[str], Any]):
    def wrapper(first_str: str, second_str: str):
        has_true_name = second_str and (second_str != first_str)
        result = function(first_str)
        if not result and has_true_name:
            result = function(second_str)
        return result
    return wrapper
