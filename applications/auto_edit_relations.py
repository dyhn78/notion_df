from db_handler.patch_handler import PatchHandler
from db_handler.parser import PageListParser as PLParser


def clone_relations(domain: PLParser, base: PLParser,
                    domain_to_target: str, domain_to_base: str, base_to_target: str):
    patch_queue = []
    for dom_id, dom_props in domain.listed_items:
        dom_patch = PatchHandler(dom_id)

        bs_id = dom_props[domain_to_base]
        bs_props = base.dicted_items_by_id[bs_id]
        tar_id = bs_props[base_to_target]
        dom_patch.append_relation(dom_props[domain_to_target], tar_id)
        patch_queue.append(dom_patch)


def find_proper_target_by_name(domain: PLParser, base: PLParser):
    pass
