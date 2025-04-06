from _scratch.icon import IconDispatcher
from notion_df.file import ExternalFile


def test_icon():
    external_file_data = {"type": "external", "name": "self.name", "external": {"url": "self_url"}}
    assert type(IconDispatcher.deserialize(external_file_data)) == ExternalFile
    assert type()
