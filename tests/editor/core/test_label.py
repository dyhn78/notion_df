from notion_zap.editor.core.label import Label, LabelKey


class MyLabel:
    a = Label()
    b = Label()
    c = Label(a)
    d = Label(b, c)
    e = Label(c, d)


class MyLabelKey(LabelKey):
    aa = MyLabel.a
    bb = MyLabel.b
    cc = MyLabel.c
    dd = MyLabel.d
    ee = MyLabel.e


def test_label():
    assert [getattr(MyLabel, key).supers for key in "abcde"] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.b, MyLabel.c},
        {MyLabel.a, MyLabel.b, MyLabel.c, MyLabel.d}
    ]


def test_label_enum():
    assert [str(getattr(MyLabelKey, key)) for key in ("aa", "bb", "cc", "dd", "ee")] == [
        "MyLabelKey(aa)",
        "MyLabelKey(bb)",
        "MyLabelKey(cc, supers=aa)",
        "MyLabelKey(dd, supers=aa, bb, cc)",
        "MyLabelKey(ee, supers=aa, bb, cc, dd)"
    ]
