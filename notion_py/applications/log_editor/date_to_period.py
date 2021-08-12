from .constants import *
from notion_py.applications.log_editor.match_property import MatchorCreatebyIndex, \
    MatchbyIndex
from notion_py.gateway.parse import PageParser
from notion_py.gateway.write import CreateTabularPage
from ..constants import ID_PERIODS


class NaljjaToGigan(MatchorCreatebyIndex):
    _target_id = ID_PERIODS
    _domain_to_target = TO_PERIODS
    _domain_index = DATES_INDEX
    _target_inbound = TITLE_PROPERTY

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
            tar_patch.props.write_rich.date('📅기간', dom_parse.start_date(),
                                            dom_parse.end_date())


class NaljjaParse:
    def __init__(self, date):
        self.parser = ParseTimeProperty(date['start'], plain_date=True)

    def get_tar(self):
        return self.parser.strf_year_and_week()

    def start_date(self):
        return self.parser.first_day_of_week()

    def end_date(self):
        return self.parser.last_day_of_week()
