from typing import Callable, Union

from notion_py.interface.parse import PageParser, PageListParser
from notion_py.interface.write import UpdateTabularPage, CreateTabularPage
from notion_py.applications.log_editor.request_structure import PropertyRequestStack


class MatchbyReference(PropertyRequestStack):
    _domain_to_target: str
    _domain_to_reference: str
    _reference_to_target: str

    def __init__(self, domain: PageListParser, reference: PageListParser):
        super().__init__(domain)
        self._reference = reference

    @classmethod
    def default(cls, domain: PageListParser, reference: PageListParser,
                domain_to_target: str, domain_to_reference: str, reference_to_target: str):
        self = cls(domain, reference)
        self._reference = reference
        self._domain_to_target = domain_to_target
        self._domain_to_reference = domain_to_reference
        self._reference_to_target = reference_to_target
        return self

    def process_unit(self, dom: PageParser):
        if dom.props[self._domain_to_target]:
            return False
        if not dom.props[self._domain_to_reference]:
            self._append_reprocess(dom)
            return True
        ref_id = self._find_ref_id(dom)
        ref_props = self._reference.search.page_by_id(ref_id)
        tar_id = ref_props[self._reference_to_target]

        dom_patch = UpdateTabularPage(dom.page_id)
        dom_patch.props.write.relation(self._domain_to_target, tar_id)
        self._append_requests(dom_patch)

    def _find_ref_id(self, dom):
        i = 0
        while True:
            try:
                ref_id = dom.props[self._domain_to_reference][i]
                break
            except KeyError:
                # 예컨대 삭제된 일지를 첫 번째 원소로 들고 있을 경우
                i += 1
        return ref_id


class MatchbyIndex(PropertyRequestStack):
    _target_id: str
    _domain_to_target: str
    _domain_index: str
    _target_inbound: str  # None 인 경우 제목 [title 속성]을 바탕으로 판단한다.
    _domain_function: Callable

    # TODO equal-to가 아니라 startswith \
    #  (예를 들어 '210625'로부터 '210625 금요일'을 찾는 것) 조건도 가능하면 좋겠다.(낮음)
    def __init__(self, domain: PageListParser, target: PageListParser):
        super().__init__(domain)
        self._target = target

    @classmethod
    def default(cls, domain: PageListParser, target: PageListParser,
                target_id: str, domain_to_target: str,
                domain_index: Union[None, str, tuple[str, None]],
                target_inbound: Union[None, str, tuple[str, None]],
                domain_function: Callable):
        self = cls(domain, target)
        self._target = target
        self._target_id = target_id
        self._domain_to_target = domain_to_target
        self._domain_index = domain_index
        self._target_inbound = target_inbound
        self._domain_function = domain_function
        return self

    def process_unit(self, dom: PageParser):
        if dom.props[self._domain_to_target]:
            return False

        if type(self._domain_index) == tuple:
            dom_index = (dom.props[index] for index in self._domain_index)
        else:
            dom_index = (dom.props[self._domain_index],)
        tar_index = self._domain_function(*dom_index)

        try:
            if self._target_inbound:
                tar_id = self._target.search.id_by_index(self._target_inbound, tar_index)
            else:
                tar_id = self._target.search.id_by_title(tar_index)
        except KeyError:
            return tar_index
        dom_patch = UpdateTabularPage(dom.page_id)
        dom_patch.props.write.relation(self._domain_to_target, [tar_id])
        self._append_requests(dom_patch)
        return False


class MatchorCreatebyIndex(MatchbyIndex):
    new_target_indices = []

    def process_unit(self, dom: PageParser):
        tar_index = super().process_unit(dom)
        if not tar_index:
            return
        self._append_reprocess(dom)

        if tar_index not in self.new_target_indices:
            tar_patch = CreateTabularPage(self._target_id)
            self._append_requests(tar_patch)
            self.new_target_indices.append(tar_index)

            tar_patch.props.write.title('📚제목', tar_index)
