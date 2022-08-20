from notion_zap.editor.core.label import Label


class MyLabel(Label):
    a = ''
    b = 0
    c = 'a'
    d = 'a', 'b'


def test_label():
    assert [getattr(MyLabel, key).supers for key in "abcde"] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.b, MyLabel.c}]
