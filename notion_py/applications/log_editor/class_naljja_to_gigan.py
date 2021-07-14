from .constant_attribute_names import *
from notion_py.applications.log_editor.match_property import MatchorCreatebyIndex, MatchbyIndex
from notion_py.interface.parse import PageParser
from notion_py.interface.write import CreateTabularPage
from ..constant_page_ids import GIGAN_ID


class NaljjaToGigan(MatchorCreatebyIndex):
    _target_id = GIGAN_ID
    _domain_to_target = TO_GIGAN
    _domain_index = NALJJA_DATE_INDEX
    _target_inbound = GIGAN_TITLE_INBOUND

    @staticmethod
    def _domain_function(date):
        return NaljjaParse(date).get_tar()

    def process_unit(self, dom: PageParser):
        tar_index = MatchbyIndex.process_unit(self, dom)
        if not tar_index:
            return
        self._append_reprocess(dom)

        if tar_index not in self.new_target_indices:
            tar_patch = CreateTabularPage(self._target_id)
            self._append_requests(tar_patch)
            self.new_target_indices.append(tar_index)

            tar_patch.props.write_rich.title('📚제목', tar_index)

            dom_parse = NaljjaParse(dom.props[self._domain_index])
            tar_patch.props.write_rich.date('📅기간', dom_parse.start_date(), dom_parse.end_date())


class NaljjaParse:
    def __init__(self, date):
        self.parser = ParseTimeProperty(date['start'], plain_date=True)

    def get_tar(self):
        return self.parser.strf_year_and_week()

    def start_date(self):
        return self.parser.first_day_of_week()

    def end_date(self):
        return self.parser.last_day_of_week()
