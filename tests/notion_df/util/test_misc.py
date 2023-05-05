import uuid

import pytest

from notion_df.util.misc import _concat_items, get_id


def test_concat_items():
    assert list(_concat_items({1: 2}, {'a': 4})) == [(1, 2), ('a', 4)]


block_uuid_dash = str(uuid.uuid4())
block_uuid_no_dash = block_uuid_dash.replace('-', '')
view_uuid_no_dash = str(uuid.uuid4()).replace('-', '')


@pytest.mark.parametrize("test_input,expected", [
    (f"https://www.notion.so/workspace-name/{block_uuid_dash}?v={view_uuid_no_dash}&pvs=4", block_uuid_dash),
    (f"https://www.notion.so/workspace-name/{block_uuid_no_dash}?v={view_uuid_no_dash}&pvs=4", block_uuid_no_dash),
    (f"https://www.notion.so/workspace-name/page-name-{block_uuid_dash}?pvs=4", block_uuid_dash),
    (f"https://www.notion.so/workspace-name/page-name-{block_uuid_dash}?pvs=4", block_uuid_dash),
    (f"www.notion.so/workspace-name/{block_uuid_dash}?v=ffc764042a4244119190932603fcb416&pvs=4", block_uuid_dash),
    (f"www.notion.so/workspace-name/{block_uuid_no_dash}?v=ffc764042a4244119190932603fcb416&pvs=4", block_uuid_no_dash),
    (f"{block_uuid_dash}?v=ffc764042a4244119190932603fcb416&pvs=4", block_uuid_dash),
    (f"{block_uuid_no_dash}?v=ffc764042a4244119190932603fcb416&pvs=4", block_uuid_no_dash),
    (block_uuid_dash, block_uuid_dash),
    (block_uuid_no_dash, block_uuid_no_dash),
])
def test_get_id(test_input, expected):
    assert get_id(test_input) == expected
