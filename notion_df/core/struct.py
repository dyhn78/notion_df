from __future__ import annotations

from typing import TypeVar, cast, Any


class Undefined:
    def __repr__(self) -> str:
        return "Undefined"

    def __bool__(self) -> bool:
        return False


undefined = Undefined()


def repr_object(obj, *attrs: Any, **kw_attrs: Any) -> str:
    def _repr(_attr_value):
        return repr(_attr_value) if isinstance(_attr_value, str) else str(_attr_value)

    attr_items = []
    for attr_value in attrs:
        if attr_value is undefined:
            continue
        attr_items.append(_repr(attr_value))
    for attr_name, attr_value in kw_attrs.items():
        if attr_value is undefined:
            continue
        attr_items.append(f"{attr_name}={_repr(attr_value)}")
    return f"{type(obj).__name__}({', '.join(attr_items)})"


T = TypeVar("T")


def force_cast(cls: type[T], obj: Any) -> T:
    assert isinstance(obj, cls)
    return cast(cls, obj)
