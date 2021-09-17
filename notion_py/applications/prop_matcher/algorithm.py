from typing import Optional, Callable

from notion_py.interface import TypeName


class MonoMatchAlgorithm:
    def __init__(self, domain: TypeName.pagelist):
        self.domain = domain

    def to_itself(self, self_ref: str):
        for dom in self.domain:
            if bool(dom.props.read_at(self_ref)):
                continue
            dom.props.write_at(self_ref, [dom.master_id])


class TernaryMatchAlgorithm:
    def __init__(self, domain: TypeName.pagelist,
                 target: TypeName.pagelist = None,
                 reference: TypeName.pagelist = None):
        self.domain = domain
        self.target = target
        self.reference = reference
        # prop_keys
        self.dom_index = 'index_as_domain'
        self.tar_index = 'index_as_target'
        self.dom_to_tar = ''
        self.dom_to_ref = ''
        self.ref_to_tar = ''
        # func by prop_key
        self.index_func: Optional[Callable] = None
        # dict by prop_value
        self.tars_by_index: dict[str, TypeName.tabular_page] = {}

    def by_ref(self, dom_to_tar, dom_to_ref, ref_to_tar):
        self.dom_to_tar = dom_to_tar
        self.dom_to_ref = dom_to_ref
        self.ref_to_tar = ref_to_tar
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_match_by_ref(dom)

    def multi_by_ref(self, dom_to_tar, dom_to_ref, ref_to_tar):
        self.dom_to_tar = dom_to_tar
        self.dom_to_ref = dom_to_ref
        self.ref_to_tar = ref_to_tar
        for dom in self.domain:
            self._try_multi_match_by_ref(dom)

    def by_index(self, dom_to_tar, index_func: Callable):
        self.dom_to_tar = dom_to_tar
        self.index_func = index_func
        self.tars_by_index = self.target.by_index_at(self.tar_index)
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_match_by_index(dom)

    def by_ref_then_index(self, dom_to_tar, dom_to_ref, ref_to_tar,
                          index_func: Callable):
        self.by_ref(dom_to_tar, dom_to_ref, ref_to_tar)
        self.by_index(dom_to_tar, index_func)

    def by_index_then_create(self, dom_to_tar, index_func: Callable,
                             tar_writer_func: Optional[Callable] = None):
        self.dom_to_tar = dom_to_tar
        self.index_func = index_func
        self.tars_by_index = self.target.by_index_at(self.tar_index)
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            if result := self._try_match_by_index_then_create(dom):
                tar, tar_index_value = result
                if tar_writer_func is not None:
                    tar_writer_func(tar, tar_index_value)
        self.target.execute()
        for dom in self.domain:
            if self._is_already_matched(dom):
                continue
            self._try_match_by_index(dom)

    def by_ref_then_index_then_create(self, dom_to_tar, dom_to_ref, ref_to_tar,
                                      index_func: Callable,
                                      tar_writer_func: Optional[Callable] = None):
        self.by_ref(dom_to_tar, dom_to_ref, ref_to_tar)
        self.by_index_then_create(dom_to_tar, index_func, tar_writer_func)

    def _is_already_matched(self, dom: TypeName.tabular_page):
        return bool(dom.props.read_at(self.dom_to_tar))

    def _try_match_by_ref(self, dom: TypeName.tabular_page):
        """
        will return False if matching is done;
        will return True or some non-empty information to put to next algorithm.
        """
        ref_ids = dom.props.read_at(self.dom_to_ref)
        for ref_id in ref_ids:
            if ref_id in self.reference.keys():
                break
        else:
            return True
        ref = self.reference.by_id[ref_id]
        tar_ids = ref.props.read_at(self.ref_to_tar)
        for tar_id in tar_ids:
            if tar_id in self.target.keys():
                break
        else:
            return True
        self._write_tar_id(dom, tar_id)

    def _try_match_by_index(self, dom: TypeName.tabular_page):
        dom_index_value = dom.props.read_at(self.dom_index)
        tar_index_value = self.index_func(dom_index_value)
        if tar_index_value not in self.tars_by_index.keys():
            return tar_index_value
        tar = self.tars_by_index[tar_index_value]
        tar_id = tar.master_id
        self._write_tar_id(dom, tar_id)

    def _try_match_by_index_then_create(self, dom: TypeName.tabular_page):
        if not (tar_index_value := self._try_match_by_index(dom)):
            return False
        tar = self.target.new_tabular_page()
        tar.props.write_at(self.tar_index, tar_index_value)
        return [tar, tar_index_value]

    def _write_tar_id(self, dom: TypeName.tabular_page, tar_id):
        values = dom.props.read_at(self.dom_to_tar)
        if tar_id in values:
            return
        else:
            values.append(tar_id)
            dom.props.write_at(self.dom_to_tar, values)

    def _try_multi_match_by_ref(self, dom: TypeName.tabular_page):
        ref_ids = dom.props.read_at(self.dom_to_ref)
        for ref_id in ref_ids:
            if ref_id in self.reference.keys():
                break
        else:
            return True
        ref = self.reference.by_id[ref_id]
        tar_ids = ref.props.read_at(self.ref_to_tar)

        values: list = dom.props.read_at(self.dom_to_tar)
        diff = False
        for tar_id in tar_ids:
            if tar_id in values:
                pass
            else:
                diff = True
                values.append(tar_id)
        if diff:
            dom.props.write_at(self.dom_to_tar, values)
