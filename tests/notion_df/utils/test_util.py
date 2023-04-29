from notion_df.utils.misc import _concat_items


def test_concat_items():
    assert list(_concat_items({1: 2}, {'a': 4})) == [(1, 2), ('a', 4)]
