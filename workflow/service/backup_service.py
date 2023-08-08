import json
from pathlib import Path
from typing import Optional

from notion_df.core.entity_core import Entity
from notion_df.core.request import Response_T
from notion_df.core.serialization import SerializationError
from notion_df.util.misc import get_generic_arg


class ResponseBackupService:
    def __init__(self, root: Path):
        self.root = root

    def _get_path(self, entity: Entity) -> Path:
        return self.root / f"{str(entity.id).replace('-', '')}.json"

    def read(self, entity: Entity[Response_T]) -> Optional[Response_T]:
        path = self._get_path(entity)
        if not path.is_file():
            return
        with path.open('r') as file:
            response_raw_data = json.load(file)
        response_cls = get_generic_arg(type(entity), Response_T)
        try:
            return response_cls.deserialize(response_raw_data)
        except SerializationError:
            print(f'Skip invalid response_raw_data: entity - {entity}, response_raw_data - {response_raw_data}')

    def write(self, entity: Entity[Response_T]) -> None:
        path = self._get_path(entity)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            print(f'\t{entity}\n\t\t-> overwrite')
        else:
            print(f'\t{entity}\n\t\t-> create')
        with path.open('w') as file:
            raw_data = entity.last_response.raw_data
            assert raw_data is not None
            json.dump(raw_data, file, indent=2)
