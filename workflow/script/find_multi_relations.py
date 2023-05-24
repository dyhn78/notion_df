from collections import defaultdict
from typing import cast

from notion_df.entity import Database
from notion_df.object.property import RelationProperty
from notion_df.variable import Settings
from workflow.constant.block_enum import DatabaseEnum

if __name__ == '__main__':
    with Settings.print:
        all_relation_properties: dict[tuple[Database, Database], list[RelationProperty]] = defaultdict(list)

        for db_enum in DatabaseEnum:
            db = db_enum.entity
            db.retrieve()
            for prop in db.properties:
                if not isinstance(prop, RelationProperty):
                    continue
                linked_db = cast(RelationProperty.database_value, db.properties[prop]).database
                all_relation_properties[(db, linked_db)].append(prop)

        for (db, linked_db), prop_list in all_relation_properties.items():
            if len(prop_list) > 1 and db.title.plain_text < linked_db.title.plain_text and DatabaseEnum.from_entity(
                    db) and DatabaseEnum.from_entity(db).name.find('depr') == -1:
                print(db.title.plain_text, linked_db.title.plain_text, prop_list)

    input()
