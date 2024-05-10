from __future__ import annotations

import re
from uuid import UUID

uuid_pattern = re.compile(r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}', re.I)
"""Regular expression to match both dashed and no-dash UUIDs."""


def get_page_or_database_id(id_or_url: str | UUID) -> UUID:
    if isinstance(id_or_url, UUID):
        return id_or_url
    match = uuid_pattern.search(id_or_url)
    if match:
        return UUID(match.group(0))
    return UUID(id_or_url)


def get_block_id(id_or_url: str | UUID) -> UUID:
    if isinstance(id_or_url, UUID):
        return id_or_url
    match = uuid_pattern.search(id_or_url.split('#')[-1])
    if match:
        return UUID(match.group(0))
    return UUID(id_or_url)


def get_page_or_database_url(id_or_url: str | UUID, workspace_name: str) -> str:
    uuid = get_page_or_database_id(id_or_url)
    return f'https://www.notion.so/{workspace_name}/' + str(uuid).replace('-', '')
