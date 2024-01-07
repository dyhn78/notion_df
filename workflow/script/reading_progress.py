from notion_df.property import PageProperties
from workflow.action.prop_matcher import event_to_reading_prop, event_to_reading_prog_prop
from workflow.block_enum import DatabaseEnum

if __name__ == '__main__':
    for event in DatabaseEnum.event_db.entity.query(event_to_reading_prog_prop.filter.is_not_empty()):
        event_readings = event.data.properties[event_to_reading_prop]
        event_readings_new = event_readings + event.data.properties[event_to_reading_prog_prop]
        if event_readings == event_readings_new:
            continue
        event.update(PageProperties({
            event_to_reading_prop: (event.data.properties[event_to_reading_prop]
                                    + event.data.properties[event_to_reading_prog_prop])
        }))
