from ..common.struct import Matcher
from ..common.helpers import find_all_unarchived_id_from_relation, \
    append_prop


class ProjectMatcher(Matcher):
    def execute(self):
        domain = self.bs.writings
        reference = self.bs.journals
        to_ref = 'to_journals'
        for dom in domain:
            for to_tar in ['to_themes', 'to_channels', 'to_readings']:
                if bool(dom.props.read_at(to_tar)):
                    continue
                ref_ids = find_all_unarchived_id_from_relation(dom, reference, to_ref)
                tar_ids = []
                for ref_id in ref_ids:
                    ref = reference.by_id[ref_id]
                    tar_ids.extend(ref.props.read_at(to_tar))
                append_prop(dom, to_tar, tar_ids)
