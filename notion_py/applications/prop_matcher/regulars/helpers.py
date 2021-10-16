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


def find_unique_target_by_idx(
        target: PageList, tar_idx, tars_by_index,
        idx_data_type='text'):
    # 1. 들고 있는 target 목록 중에서 찾는다.
    if tar := tars_by_index.get(tar_idx):
        return tar
    # 2. idx 값을 바탕으로 쿼리한다.
    tar_query = target.open_query()
    maker = tar_query.make_filter.at('index_as_target', idx_data_type)
    ft = maker.equals(tar_idx)
    tar_query.push_filter(ft)
    tar_query.execute()
    if tar := tars_by_index.get(tar_idx):
        return tar
    return ''


def create_unique_target_by_idx(target: PageList, tar_idx):
    tar = target.create_tabular_page()
    tar.props.write_at('index_as_target', tar_idx)
    return tar
