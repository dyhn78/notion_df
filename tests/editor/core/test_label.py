import logging
import sys

from notion_zap.editor.core.label import Label

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class MyLabel(Label):
    a = ''
    b = 0
    c = 'a'
    d = 'a', 'b'


def test_label():
    print([label for label in MyLabel])
    assert [label.supers for label in MyLabel] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.b, MyLabel.c}]
