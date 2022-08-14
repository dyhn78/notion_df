from notion_zap.editor.core.label import LabelEnum


class MyLabelEnum(LabelEnum):
    a = 0
    b = 0
    c = a
    d = a, b
    e = c, d


def test_label_enum():
    assert MyLabelEnum.a.value
