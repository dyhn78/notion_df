from __future__ import annotations

from typing import Hashable

from notion_zap.apps.prop_matcher.struct import RowEditor
from notion_zap.cli.editors import PageRow, Database


def has_value(row: PageRow, tag_target):
    return bool(row.read_tag(tag_target))


def set_value(row: PageRow, target: PageRow, tag_target):
    row.write_relation(tag=tag_target, value=target.block_id)


class ReferenceInfo:
    def __init__(
            self, reference: Database, tag_ref: Hashable, refs_tag_tar: Hashable):
        self.reference = reference
        self.tag_ref = tag_ref
        self.refs_tag_tar = refs_tag_tar


class GetterByReference(RowEditor):
    def __init__(self, target: Database, ref_info: ReferenceInfo):
        self.target = target
        self.ref_info = ref_info

    def __call__(self, row: PageRow):
        if ref := get_unique_page_from_relation(row, self.ref_info.reference, self.ref_info.tag_ref):
            if tar := get_unique_page_from_relation(ref, self.target, self.ref_info.refs_tag_tar):
                return tar
            return None


def write_extendedly(row: PageRow, prop_tag: str, values: list[str]):
    old_values = row.read_tag(prop_tag)
    changed = False
    for value in values:
        if value not in old_values:
            old_values.append(value)
            changed = True
    if changed:
        row.write(tag=prop_tag, value=old_values)
    return True


def get_unique_page_from_relation(row: PageRow, target: Database, tag_tar):
    tar_ids = row.read_tag(tag_tar)
    for tar_id in tar_ids:
        if tar := target.rows.fetch_page(tar_id):
            return tar
    return None


def get_all_pages_from_relation(
        row: PageRow, target: Database,
        tag_tar: Hashable) -> list[PageRow]:
    tar_ids = row.read_tag(tag_tar)
    res = []
    for tar_id in tar_ids:
        if tar := target.rows.fetch_page(tar_id):
            res.append(tar)
    return res


def query_unique_page_by_idx(
        database: Database, idx, tag_idx: str,
        prop_type='text'):
    """
    idx: value of index property
    tag_idx: key alias of the property
    prop_type: notion-type of the property
    """
    query = database.rows.open_query()
    manager = query.filter_manager_by_tags(tag_idx, prop_type)
    ft = manager.equals(idx)
    query.push_filter(ft)
    tars = query.execute()
    if tars:
        return tars[0]
    return None
