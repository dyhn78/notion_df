from __future__ import annotations

from enum import Enum
from typing import Iterable, cast, Any, Optional


class Label(Enum):
    # TODO: change "superlabels" arg to "Self" after python 3.11
    def __init__(self, description: Any, *superlabels: Label | Iterable[Label]):
        print(self, [f"({type(label)}: {label})" for label in superlabels])
        if not description:
            pass  # TODO: fill the description with str(self)
        self._value_ = description
        self.superlabels: set[Label] = set()
        superlabel_values = self._parse_superlabel_input(superlabels)
        for superlabel in superlabel_values:
            self._recursively_add_superlabels(superlabel)

    def _recursively_add_superlabels(self, superlabel: Label):
        if superlabel in self.superlabels:
            return
        self.superlabels.add(superlabel)
        for super_superlabel in superlabel.superlabels:
            self._recursively_add_superlabels(super_superlabel)

    def _parse_superlabel_input(self, superlabel_input: tuple[Label | Iterable[Label]]) -> Iterable[Label]:
        cls = type(self)

        def parse_label_input(label_key: Label | Any) -> Optional[Label]:
            if isinstance(label_key, cls):
                return label_key
            try:

                return cls[label_key]
            except KeyError:
                pass
            return None

        def is_labels_iterable(label_keys) -> Optional[list[Label]]:
            _labels = []
            for label_key in label_keys:
                print(f"\t{label_keys=}, {label_key=}")
                if label := parse_label_input(label_key):
                    _labels.append(label)
                else:
                    return None
            return _labels

        try:
            if (labels := is_labels_iterable(superlabel_input)) is not None:
                return labels
            if len(superlabel_input) == 1 and (labels := is_labels_iterable(superlabel_input[0])) is not None:
                return labels
            labels = "ERROR"
            raise ValueError
            # raise ValueError(f"{self=}, {superlabel_input=}")
        finally:
            print(f"{self=}, {superlabel_input=}, {labels=}")

    @property
    def value(self) -> Label:
        return cast(Label, super().value)
