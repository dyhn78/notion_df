import json
from pathlib import Path
from typing import Optional

from loguru import logger

from notion_df.core.data_core import EntityDataT
from notion_df.core.entity_core import Entity
from notion_df.core.serialization import SerializationError


class ResponseBackupService:
    def __init__(self, root: Path):
        self.root = root

    def _get_path(self, entity: Entity) -> Path:
        return self.root / f"{str(entity.id).replace('-', '')}.json"

    def read(self, entity: Entity[EntityDataT]) -> Optional[EntityDataT]:
        path = self._get_path(entity)
        if not path.is_file():
            return None
        response_raw_data = json.loads(path.read_text())
        response_cls = entity.get_data_cls()
        try:
            return response_cls.deserialize(response_raw_data)
        except SerializationError:
            logger.warning(
                f"Skip invalid response_raw_data: entity - {entity}, response_raw_data - {response_raw_data}"
            )

    def write(self, entity: Entity[EntityDataT]) -> None:
        path = self._get_path(entity)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            logger.info(f"\t{entity}\n\t\t-> overwrite")
        else:
            logger.info(f"\t{entity}\n\t\t-> create")
        with path.open("w") as file:
            raw_data = entity.data.raw
            assert raw_data is not None
            json.dump(raw_data, file, indent=2)
