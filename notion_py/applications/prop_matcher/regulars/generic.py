from notion_py.applications.prop_matcher.common.helpers import overwrite_prop
from notion_py.applications.prop_matcher.regulars.helpers import \
    find_unique_target_id_by_homo_ref, create_unique_target_by_idx, \
    find_unique_target_id_by_ref, \
    find_unique_target_by_idx


class GenericAlgorithms:
    @staticmethod
    def uniquely_with_homo_ref_and_idx(domain, target, to_tar, idx_parser,
                                       tars_by_index):
        for dom in domain:
            if bool(dom.props.read_at(to_tar)):
                continue
            if tar_id := find_unique_target_id_by_homo_ref(dom, domain, target, to_tar):
                pass
            else:
                dom_idx = dom.props.read_at('index_as_domain')
                tar_idx = idx_parser(dom_idx)
                if tar := find_unique_target_by_idx(target, tar_idx, tars_by_index):
                    pass
                else:
                    tar = create_unique_target_by_idx(target, tar_idx)
                    tar.execute()
                tar_id = tar.master_id
            overwrite_prop(dom, to_tar, tar_id)

    @staticmethod
    def uniquely_with_hetero_ref_and_idx(
            domain, reference, target, to_ref, to_tar, idx_parser, tars_by_index):
        for dom in domain:
            if bool(dom.props.read_at(to_tar)):
                continue
            if tar_id := find_unique_target_id_by_ref(dom, reference, target, to_ref,
                                                      to_tar):
                pass
            else:
                dom_idx = dom.props.read_at('index_as_domain')
                tar_idx = idx_parser(dom_idx)
                if tar := find_unique_target_by_idx(target, tar_idx, tars_by_index):
                    pass
                else:
                    tar = create_unique_target_by_idx(target, tar_idx)
                    tar.execute()
                tar_id = tar.master_id
            overwrite_prop(dom, to_tar, tar_id)
