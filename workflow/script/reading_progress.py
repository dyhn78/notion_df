from notion_df.property import PageProperties
from workflow.action.prop_matcher import event_to_reading_prop, event_to_reading_prog_prop
from workflow.block_enum import DatabaseEnum

if __name__ == '__main__':
    for event in DatabaseEnum.event_db.entity.query(event_to_reading_prog_prop.filter.is_not_empty()):
        event.update(PageProperties({
            event_to_reading_prop: (event.data.properties[event_to_reading_prop]
                                    + event.data.properties[event_to_reading_prog_prop])
        }))
