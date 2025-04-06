from inspect import isabstract

import pytest

from _scratch.icon import Icon, File, Emoji, InternalFile, ExternalFile
from _scratch.serialization import registry__get_dispatch_cls, Deserializable


@pytest.mark.parametrize("cls", [Icon, File, Emoji, InternalFile, ExternalFile])
def test_deserializable_classes(cls: type[Deserializable]):
    if isabstract(cls):
        assert cls in registry__get_dispatch_cls
