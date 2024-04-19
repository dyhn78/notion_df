from __future__ import annotations

from typing import Iterable, Any

from loguru import logger


class DeprCreateDateEvent(MatchSequentialAction):
    event_db = DatabaseEnum.event_db.entity
    target_to_datei_prop = RelationProperty(DatabaseEnum.datei_db.prefix_title)
    target_to_event_prop = RelationProperty(DatabaseEnum.event_db.prefix_title)
    # target_to_event_prog_prop = RelationProperty(DatabaseEnum.event_db.prefix + '진도')

    def __init__(self, base: MatchActionBase, target_db: DatabaseEnum):
        super().__init__(base)
        self.target_db = target_db.entity
        self.event_to_target_prog_prop = RelationProperty(target_db.prefix + '진도')
        self.event_to_target_prop = RelationProperty(target_db.prefix_title)

    def __repr__(self):
        return repr_object(self,
                           target_db=self.target_db)

    def query(self) -> Iterable[Page]:
        return self.target_db.query(
            filter=self.target_to_datei_prop.filter.is_not_empty())

    def process_page(self, target: Page) -> Any:
        if target.data.parent != self.target_db:
            return
        datei_list = target.data.properties[self.target_to_datei_prop]
        datei_without_event_list = set(datei_list)
        for event in target.data.properties[self.target_to_event_prop]:
            for datei in event.get_data().properties[event_to_datei_prop]:
                datei_without_event_list.discard(datei)
        logger.info(f'{target=}, {datei_without_event_list=}')

        for datei in datei_without_event_list:
            event = self.event_db.create_child_page(PageProperties({
                self.event_to_target_prop: self.event_to_target_prop.page_value(
                    [target]),
                event_to_datei_prop: event_to_datei_prop.page_value([datei]),
                event_title_prop: event_title_prop.page_value.from_plain_text(
                    self.date_namespace.strf_date(datei))
            }))
            logger.info(f'{target=}, {event=}')


class DeprMatchRecordTopic(MatchSequentialAction):
    def __init__(self, base: MatchActionBase, record: DatabaseEnum, ref: DatabaseEnum,
                 record_to_ref_prop_name: str, record_to_topic_prop_name: str,
                 ref_to_topic_prop_name: str):
        super().__init__(base)
        self.record_db = record.entity
        self.ref_db = ref.entity
        self.record_to_ref_prop = RelationProperty(record_to_ref_prop_name)
        self.record_to_topic_prop = RelationProperty(record_to_topic_prop_name)
        self.ref_to_topic_prop = RelationProperty(ref_to_topic_prop_name)

    def query(self) -> Iterable[Page]:
        return self.record_db.query(self.record_to_ref_prop.filter.is_not_empty())

    def process_page(self, record: Page) -> None:
        if not (record.data.parent == self.record_db
                and record.data.properties[self.record_to_ref_prop]):
            return

        # TODO: rewrite so that it utilizes the RelationPagePropertyValue's feature
        #  (rather than based on builtin list and set)
        curr_topic_list: list[Page] = list(
            record.data.properties[self.record_to_topic_prop])
        new_topic_set: set[Page] = set(curr_topic_list)
        for ref in record.data.properties[self.record_to_ref_prop]:
            ref_topic_set = {topic for topic in
                             ref.get_data().properties[self.ref_to_topic_prop]
                             if topic.get_data().properties[
                                 topic_base_type_prop] == topic_base_type_progress}
            if set(curr_topic_list) & ref_topic_set:
                continue
            new_topic_set.update(ref_topic_set)
        if not new_topic_set - set(curr_topic_list):
            return
        curr_topic_list = list(
            record.retrieve().data.properties[self.record_to_topic_prop])
        new_topic = curr_topic_list + list(new_topic_set)
        record.update(PageProperties({
            self.record_to_topic_prop: self.record_to_topic_prop.page_value(
                new_topic)}))
