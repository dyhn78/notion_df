from notion_zap.cli import editors


def extend_prop(dom: editors.PageRow, prop_tag: str, values: list[str]):
    old_values = dom.props.read_tag(prop_tag)
    changed = False
    for value in values:
        if value not in old_values:
            old_values.append(value)
            changed = True
    if changed:
        dom.props.write_at(prop_tag, old_values)
    return True


def fetch_unique_page_of_relation(
        dom: editors.PageRow, target: editors.Database, to_tar: str):
    tar_ids = dom.props.read_tag(to_tar)
    for tar_id in tar_ids:
        if tar := target.rows.fetch(tar_id):
            return tar
    return None


def fetch_all_pages_of_relation(
        dom: editors.PageRow, target: editors.Database,
        to_tar: str) -> list[editors.PageRow]:
    tar_ids = dom.props.read_tag(to_tar)
    res = []
    for tar_id in tar_ids:
        if tar := target.rows.fetch(tar_id):
            res.append(tar)
    return res


def query_unique_page_by_idx(
        database: editors.Database, idx, idx_tag: str,
        prop_type='text'):
    query = database.rows.open_query()
    maker = query.filter_maker.at(idx_tag, prop_type)
    ft = maker.equals(idx)
    query.push_filter(ft)
    tars = query.execute()
    if tars:
        return tars[0]
    return None


# def fetch_unique_unarchived_id_from_relation(
#         dom: editors.PageRow, target: editors.RowChildren, to_tar: str) -> str:
#     tar_ids = dom.props.read_at(to_tar)
#     for tar_id in tar_ids:
#         tar = target.fetch_one(tar_id)
#         if tar is not None and not tar.archived:
#             return tar_id
#     return ''


# def fetch_all_unarchived_id_from_relation(
#         dom: editors.PageRow, target: editors.RowChildren, to_tar: str) -> list[str]:
#     tar_ids = dom.props.read_at(to_tar)
#     res = []
#     for tar_id in tar_ids:
#         if tar_id in target.ids():
#             res.append(tar_id)
#             continue
#         tar = target.fetch_one(tar_id)
#         if tar is not None and not tar.archived:
#             res.append(tar.block_id)
#             continue
#     return res
#
#
# def find_unique_target_id_by_homo_ref(
#         dom: editors.PageRow, domain: editors.RowChildren,
#         target: editors.RowChildren, to_tar: str):
#     return find_unique_target_id_by_ref(dom, domain, target, 'up_self', to_tar)
#
#
# def find_unique_target_id_by_ref(
#         dom: editors.PageRow, reference: editors.RowChildren, target: editors.RowChildren,
#         Tdoms_ref: str, to_tar: str):
#     if ref_id := fetch_unique_unarchived_id_from_relation(dom, reference, Tdoms_ref):
#         ref = reference.by_id[ref_id]
#         if tar_id := fetch_unique_unarchived_id_from_relation(ref, target, to_tar):
#             return tar_id
#     return ''
