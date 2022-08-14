from notion_zap.editor.core.label import Label, LabelEnum


class MyLabel:
    a = Label()
    b = Label()
    c = Label(a)
    d = Label(b, c)
    e = Label(c, d)


class MyLabelEnum(LabelEnum):
    aa = MyLabel.a
    bb = MyLabel.b
    cc = MyLabel.c
    dd = MyLabel.d
    ee = MyLabel.e


class MyLabelEnum2(LabelEnum):
    a = Label()
    b = Label()
    c = Label(a)
    d = Label(b, c)
    e = Label(c, d)


def test_label():
    assert [getattr(MyLabel, key).supers for key in "abcde"] == [
        set(), set(), {MyLabel.a}, {MyLabel.a, MyLabel.b, MyLabel.c},
        {MyLabel.a, MyLabel.b, MyLabel.c, MyLabel.d}
    ]


def test_label_enum():
    assert [str(getattr(MyLabelEnum, key)) for key in ("aa", "bb", "cc", "dd", "ee")] == [
        "MyLabelEnum(aa)",
        "MyLabelEnum(bb)",
        "MyLabelEnum(cc; supers=aa)",
        "MyLabelEnum(dd; supers=aa, bb, cc)",
        "MyLabelEnum(ee; supers=aa, bb, cc, dd)"
    ]
    assert [str(getattr(MyLabelEnum2, key)) for key in "abcde"] == [
        "MyLabelEnum2(a)",
        "MyLabelEnum2(b)",
        "MyLabelEnum2(c; supers=a)",
        "MyLabelEnum2(d; supers=a, b, c)",
        "MyLabelEnum2(e; supers=a, b, c, d)"
    ]
