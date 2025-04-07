from _scratch.icon import Icon, File, ExternalFile


def test_icon():
    external_file_data = {"type": "external", "name": "self.name", "external": {"url": "self_url"}}
    assert type(Icon.deserialize(external_file_data)) == ExternalFile
    assert Icon.deserialize(external_file_data) == File.deserialize(external_file_data) == ExternalFile.deserialize(
        external_file_data)
