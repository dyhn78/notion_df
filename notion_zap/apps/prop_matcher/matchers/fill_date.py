from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DateObject
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter


class DateIntroducer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, date: PageRow, date_title=None):
        """provide date_title manually if yet not synced to server-side"""
        if date_title is None:
            date_title = date.read_key_alias('title')
        date_handler = DateFormatter.from_strf_dig6(date_title)
        new_tar_idx = date_handler.stringify_date()
        if date_title != new_tar_idx:
            date.write(key_alias='title', value=new_tar_idx)
        date_range = DateObject(date_handler.date)
        if date_range != date.read_key_alias('dateval_manual'):
            date.write_date(key_alias='dateval_manual', value=date_range)
        date.save()
