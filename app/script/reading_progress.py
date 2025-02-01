from app.my_block import DatabaseEnum
from notion_df.property import PageProperties, RelationProperty

summit_datei1_prop = RelationProperty("🟣일간")
summit_datei2_prop = RelationProperty("🟣생성")

if __name__ == "__main__":
    for summit in DatabaseEnum.heart_db.entity.query(
        summit_datei2_prop.filter.is_not_empty()
    ):
        summit_datei1 = summit.data.properties[summit_datei1_prop]
        summit_datei1_new = summit_datei1 + summit.data.properties[summit_datei2_prop]
        if summit_datei1 == summit_datei1_new:
            continue
        summit.update(
            PageProperties(
                {
                    summit_datei1_prop: summit_datei1_new,
                    summit_datei2_prop: summit_datei2_prop.page_value(),
                }
            )
        )
