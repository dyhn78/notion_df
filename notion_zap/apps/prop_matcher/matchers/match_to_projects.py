from ..common.base import Matcher
from ..common.helpers import append_prop, fetch_all_pages_from_relation


class ProjectMatcher(Matcher):
    def execute(self):
        domain = self.bs.writings
        reference = self.bs.journals
        to_ref = 'to_journals'
        to_tars = ['to_themes', 'to_channels', 'to_readings']
        for dom in domain:
            for to_tar in to_tars:
                if bool(dom.props.read_at(to_tar)):
                    continue
                refs = fetch_all_pages_from_relation(dom, reference, to_ref)
                tar_ids = []
                for ref in refs:
                    tar_ids.extend(ref.props.read_at(to_tar))
                append_prop(dom, to_tar, tar_ids)
