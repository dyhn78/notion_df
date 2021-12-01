# match parser_type to data_types
PAGE_TYPES = {"child_page"}
_DOCUMENT_TYPES = {"paragraph", "bulleted_list_item",
                   "numbered_list_item", "toggle", "to_do"}
TEXT_TYPES = _DOCUMENT_TYPES | {"heading_1", "heading_2", "heading_3"}
CAN_HAVE_CHILDREN = PAGE_TYPES | _DOCUMENT_TYPES
SUPPORTED = TEXT_TYPES | PAGE_TYPES
UNSUPPORTED = {"unsupported"}
