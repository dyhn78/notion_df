from ..common import DateFormat, PropertyFrame, PropertyFrameUnit
from ..requestor import Query
from .inline.page_block import InlinePageBlock
from .inline.text_block import TextBlock
from .tabular.database import Database
from .tabular.page import TabularPageBlock
from .tabular.pagelist import PageList


class TypeName:
    database = Database
    tabular_page = TabularPageBlock
    inline_page = InlinePageBlock
    text_block = TextBlock

    pagelist = PageList
    query = Query

    date_format = DateFormat
    frame = PropertyFrame
    frame_unit = PropertyFrameUnit
