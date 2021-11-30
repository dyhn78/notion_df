import re


def id_to_url(uuid: str, preview=False):
    uuid = uuid.replace('-', '')
    url = 'https://www.notion.so/dyhn/' + uuid
    if preview:
        print(url)
    return url


def url_to_id(uuid_or_url: str):
    prefixes = ['https://www.notion.so/', 'www.notion.so/']
    for prefix in prefixes:
        uuid_or_url = uuid_or_url.replace(prefix, '')
    uuid = _clean_uuid(uuid_or_url)
    uuid = uuid.replace('-', '')
    # assert len(uuid) == 32
    return uuid


def _clean_uuid(user_plus_uuid: str):
    block_id = re.compile(r'^[\w\d-]+$')
    if id_match := block_id.match(user_plus_uuid):
        return id_match.group(0)
    user_and_id = re.compile(r'^[\w\d]+[/]([\w\d-]+)')
    if match := user_and_id.match(user_plus_uuid):
        return match.group(1)
    raise ValueError(user_plus_uuid)


if __name__ == '__main__':
    id_to_url('961d1ca0a3d24a46b838ba85e710f18d', preview=True)
