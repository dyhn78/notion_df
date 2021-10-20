from notion_py.interface.editor.tabular import PageList, TabularPageBlock
from ..common.helpers import find_unique_unarchived_id_from_relation


def find_unique_target_id_by_homo_ref(
        dom: TabularPageBlock, domain: PageList, target: PageList, to_tar: str):
    return find_unique_target_id_by_ref(dom, domain, target, 'up_self', to_tar)


def find_unique_target_id_by_ref(
        dom: TabularPageBlock, reference: PageList, target: PageList,
        to_ref: str, to_tar: str):
    if ref_id := find_unique_unarchived_id_from_relation(dom, reference, to_ref):
        ref = reference.by_id[ref_id]
        if tar_id := find_unique_unarchived_id_from_relation(ref, target, to_tar):
            return tar_id
    return ''


def query_target_by_idx(
        target: PageList, tar_idx,
        idx_data_type='text'):
    tar_query = target.open_query()
    maker = tar_query.make_filter.at('index_as_target', idx_data_type)
    ft = maker.equals(tar_idx)
    tar_query.push_filter(ft)
    tars = tar_query.execute()
    if tars:
        assert len(tars) == 1
        return tars[0]
    return None


def create_unique_tar_by_idx(target: PageList, tar_idx):
    tar = target.create_tabular_page()
    tar.props.write_at('index_as_target', tar_idx)
    return tar
