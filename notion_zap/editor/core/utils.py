from typing import Iterable


def repr_object(self, args: Iterable[str]) -> str:
    return f"{type(self).__name__}({', '.join(args)})"


def get_num_iterator():
    num = 0
    while True:
        yield num
        num += 1
