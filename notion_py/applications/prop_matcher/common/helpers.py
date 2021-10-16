from notion_client import APIResponseError

from notion_py.interface import RootEditor
from notion_py.interface.editor.tabular import PageList, TabularPageBlock


def overwrite_prop(dom, prop_tag: str, value: str):
    old_value = dom.props.read_at(prop_tag)
    if value == old_value:
        return False
    else:
        dom.props.write_at(prop_tag, value)
        return True


def append_prop(dom, prop_tag: str, values: list[str]):
    old_values = dom.props.read_at(prop_tag)
    for value in values:
        if value not in old_values:
            old_values.append(value)
    dom.props.write_at(prop_tag, old_values)
    return True


def find_unique_unarchived_id_from_relation(dom: TabularPageBlock, targets: PageList,
                                            to_tar: str) -> str:
    tar_ids = dom.props.read_at(to_tar)
    for tar_id in tar_ids:
        if tar_id in targets.ids():
            break
        tar = targets.fetch_a_child(tar_id)
        if tar is not None and not tar.archived:
            tar_id = tar.master_id
            break
    else:
        return ''
    return tar_id


def find_all_unarchived_id_from_relation(dom: TabularPageBlock, targets: PageList,
                                         to_tar: str) -> list[str]:
    tar_ids = dom.props.read_at(to_tar)
    res = []
    for tar_id in tar_ids:
        if tar_id in targets.ids():
            res.append(tar_id)
            continue
        tar = targets.fetch_a_child(tar_id)
        if tar is not None and not tar.archived:
            res.append(tar.master_id)
            continue
    return res

