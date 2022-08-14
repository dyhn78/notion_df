from notion_zap.editor.core.label import Label


class MyLabel(Label):
    a = 'aa'
    b = 'bb'
    c = 'cc', a
    d = 'dd', b, c
    e = 'ee', c, d


def test_label_enum():
    assert [label.superlabels for label in MyLabel] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.b, MyLabel.c},
        {MyLabel.a, MyLabel.b, MyLabel.c, MyLabel.d}
    ]
