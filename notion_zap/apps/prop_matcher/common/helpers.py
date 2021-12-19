from notion_zap.cli import editors


def extend_prop(dom: editors.PageRow, prop_tag: str, values: list[str]):
    old_values = dom.read_tag(prop_tag)
    changed = False
    for value in values:
        if value not in old_values:
            old_values.append(value)
            changed = True
    if changed:
        dom.write(tag=prop_tag, value=old_values)
    return True


def fetch_unique_page_of_relation(
        dom: editors.PageRow, target: editors.Database, to_tar: str):
    tar_ids = dom.read_tag(to_tar)
    for tar_id in tar_ids:
        if tar := target.rows.fetch_page(tar_id):
            return tar
    return None


def fetch_all_pages_of_relation(
        dom: editors.PageRow, target: editors.Database,
        to_tar: str) -> list[editors.PageRow]:
    tar_ids = dom.read_tag(to_tar)
    res = []
    for tar_id in tar_ids:
        if tar := target.rows.fetch_page(tar_id):
            res.append(tar)
    return res


def query_unique_page_by_idx(
        database: editors.Database, idx, idx_tag: str,
        prop_type='text'):
    query = database.rows.open_query()
    maker = query.filter_manager_by_tags(idx_tag, prop_type)
    ft = maker.equals(idx)
    query.push_filter(ft)
    tars = query.execute()
    if tars:
        return tars[0]
    return None
