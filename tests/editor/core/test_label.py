import logging
import sys

from notion_zap.editor.frame.depr.label import Label

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class MyLabel(Label):
    a = ''
    b = 0
    c = 'a'
    d = 'a', 'c'


def test_label():
    assert [set(label.supers) for label in MyLabel] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.c}]
