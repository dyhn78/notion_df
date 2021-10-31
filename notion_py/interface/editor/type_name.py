from .inline.page_item import PageItem
from .inline.text_block import TextItem
from .tabular.database import Database
from .tabular.page import PageRow
from .tabular.pagelist import PageList
from ..common import DateFormat, PropertyFrame, PropertyFrameUnit
from ..requestor import Query


class TypeName:
    database = Database
    tabular_page = PageRow
    inline_page = PageItem
    text_block = TextItem

    pagelist = PageList
    query = Query

    date_format = DateFormat
    frame = PropertyFrame
    frame_unit = PropertyFrameUnit
