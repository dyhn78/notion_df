from typing import Callable, Union

from interface.parse.databases import PageListParser
from interface.parse.pages import PagePropertyParser
from applications.process.handler import PropertyHandler
from interface.requests.edit import DatabaseUpdate, DatabaseCreate


class MatchbyReference(PropertyHandler):
    def __init__(self, domain: PageListParser, reference: PageListParser,
                 domain_to_target: str, domain_to_reference: str, reference_to_target: str):
        super().__init__(domain)
        self._reference = reference
        self._domain_to_target = domain_to_target
        self._domain_to_reference = domain_to_reference
        self._reference_to_target = reference_to_target

    def _process_unit(self, dom: PagePropertyParser):
        if dom.props[self._domain_to_target]:
            return False
        if not dom.props[self._domain_to_reference]:
            self._append_reprocess(dom)
            return True

        ref_id = dom.props[self._domain_to_reference][0]
        ref_props = self._reference.dict_by_id[ref_id]
        tar_id = ref_props[self._reference_to_target]

        dom_patch = DatabaseUpdate(dom.id)
        dom_patch.props.add_relation(self._domain_to_target, tar_id)
        self._append_requests(dom_patch)


class MatchbyIndex(PropertyHandler):
    """
    :param target_index: None 인 경우 제목 [title 속성]을 바탕으로 판단한다.
    """
    # TODO equal-to가 아니라 startswith \
    #  (예를 들어 '210625'로부터 '210625 금요일'을 찾는 것) 조건도 가능하면 좋겠다.(낮음)
    def __init__(self, domain: PageListParser, target: PageListParser,
                 domain_to_target: str, domain_function: Callable,
                 domain_index: Union[None, str, tuple[str, None]],
                 target_index: Union[None, str, tuple[str, None]]):
        super().__init__(domain)
        self._target = target
        self._domain_to_target = domain_to_target
        self._domain_index = domain_index
        self._target_index = target_index
        self._domain_function = domain_function

    def _process_unit(self, dom: PagePropertyParser):
        if dom.props[self._domain_to_target]:
            return False

        if self._target_index:
            target_indices = self._target.index_to_id(self._target_index)
        else:
            target_indices = self._target.title_to_id

        if type(self._domain_index) == tuple:
            dom_index = (dom.props[index] for index in self._domain_index)
        else:
            dom_index = (dom.props[self._domain_index], )
        tar_index = self._domain_function(*dom_index)

        if tar_index not in target_indices:
            return tar_index
        else:
            tar_id = self._target.title_to_id[tar_index]
            dom_patch = DatabaseUpdate(dom.id)
            dom_patch.props.add_relation(self._domain_to_target, [tar_id])
            self._append_requests(dom_patch)
            return False


class MatchorCreatebyIndex(MatchbyIndex):
    def __init__(self, domain: PageListParser, target: PageListParser, target_id: str,
                 domain_to_target: str, domain_function: Callable,
                 domain_index: Union[None, str, tuple[str, None]],
                 target_index: Union[None, str, tuple[str, None]]):
        super().__init__(domain, target, domain_to_target, domain_function, domain_index, target_index)
        self._target_id = target_id

    def _process_unit(self, dom: PagePropertyParser):
        # TODO : reprocess와 process 사이에서 무한 루프가 돌고 있다. 없애야 한다. (최상)
        tar_index = super()._process_unit(dom)
        if not tar_index:
            return
        tar_patch = DatabaseCreate(self._target_id)
        tar_patch.props.add_title(tar_index)
        self._append_requests(tar_patch)
        self._append_reprocess(dom)
