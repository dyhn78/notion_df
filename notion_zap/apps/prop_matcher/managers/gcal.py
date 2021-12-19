import datetime as dt
from abc import ABCMeta
from typing import Optional

# noinspection PyPackageRequirements
from googleapiclient.errors import HttpError

import notion_zap.apps.externals.gcal
from notion_zap.cli import editors
from notion_zap.cli.structs import DateObject
from .dates import DateMatcherAbs
from ..common.dt_handler import TimeStringHandler
from ..common.helpers import query_unique_page_by_idx
from ..common.struct import EditorManager


class GcalMatcherAbs(EditorManager, metaclass=ABCMeta):
    Gcals = notion_zap.apps.externals.gcal.events
    Gcal_api_error = HttpError

    def __init__(self, bs):
        super().__init__(bs)


class _GcalScheduleMatcherAbs(GcalMatcherAbs, DateMatcherAbs, metaclass=ABCMeta):
    T_tar = 'to_scheduled_dates'
    Ttimestr = 'timestr'
    Ttitle = 'title'
    Tis_synced = 'gcal_sync_status'
    Tgcal_link = 'gcal_link'
    Tgcal_id = 'gcal_id'

    def __init__(self, bs, calendar_id='primary'):
        GcalMatcherAbs.__init__(self, bs)
        DateMatcherAbs.__init__(self, bs)
        self.domain = self.bs.schedules
        self.domain_by_idx = self.domain.rows.index_by_tag(self.Tgcal_id)
        self.calendar_id = calendar_id


class GcaltoScheduleMatcher(_GcalScheduleMatcherAbs):
    def __init__(self, bs, calendar_id='primary', updated_in_past_x_days=7):
        super().__init__(bs, calendar_id)
        if updated_in_past_x_days:
            self.updated_min = (
                    dt.datetime.now() -
                    dt.timedelta(days=updated_in_past_x_days)
            ).astimezone()
        else:
            self.updated_min = None

    def execute(self):
        events = self.Gcals.EventLister(
            calendar_id=self.calendar_id,
            only_single_events=True,
            updated_min=self.updated_min,
        ).execute()
        for event in events:
            self.sync_gcal_to_dom(event)

    def sync_gcal_to_dom(self, event):
        if dom := self.find_dom_by_gcal(event):
            if dom.last_edited_time < event['updated']:
                self.update_dom(dom, event)
        else:
            self.create_dom(event)

    def find_dom_by_gcal(self, event):
        idx = event['id']
        if dom := self.domain_by_idx.get(idx):
            return dom
        if dom := query_unique_page_by_idx(
                self.domain, idx, self.Tgcal_id, 'text'):
            return dom
        return None

    def update_dom(self, dom: editors.PageRow, event):
        property_writer = dom
        property_writer.write_checkbox(tag=self.Tis_synced, value=True)
        if summary := event.get('summary'):
            writer = dom
            writer.write_title(tag=self.Ttitle, value=summary)
        try:
            dt_start = dt.datetime.fromisoformat(event['start']['dateTime'])
            dt_end = dt.datetime.fromisoformat(event['end']['dateTime'])
            self.set_date_targets(dom, dt_start.date(), dt_end.date())
            self.set_timestr(dom, dt_start.time(), dt_end.time())
        except KeyError:
            date_start = dt.date.fromisoformat(event['start']['date'])
            date_end = dt.date.fromisoformat(event['end']['date'])
            self.set_date_targets(dom, date_start, date_end - dt.timedelta(days=1))
        dom.save()

    def create_dom(self, event):
        dom = self.domain.open_new_page()
        dom.write_text(tag=self.Tgcal_id, value=event['id'])
        self.domain_by_idx.get(event['id'])
        dom.write_url(tag=self.Tgcal_link, value=event['htmlLink'])
        self.update_dom(dom, event)

    def set_date_targets(self, dom: editors.PageRow,
                         date_start: dt.date, date_end: dt.date):
        def iter_date():
            now = date_start
            while now <= date_end:
                yield now
                now += dt.timedelta(days=1)

        tar_ids = []
        for date_val in iter_date():
            tar = self.find_or_create_tar_by_date(date_val)
            tar_ids.append(tar.block_id)
        if tar_ids != dom.read_tag(self.T_tar):
            dom.write_relation(tag=self.T_tar, value=tar_ids)

    def set_timestr(self, dom: editors.PageRow,
                    start: dt.time, end: Optional[dt.time] = None):
        timestr = dom.get_tag(self.Ttimestr, '')
        new_timestr = TimeStringHandler(timestr).replace(start, end)
        if timestr != new_timestr:
            dom.write_text(tag=self.Ttimestr, value=new_timestr)


class GcalfromScheduleMatcher(_GcalScheduleMatcherAbs):
    def __init__(self, bs, calendar_id='primary', default_event_duration_in_minutes=60):
        super().__init__(bs, calendar_id)
        self.default_event_duration = default_event_duration_in_minutes

    def execute(self):
        for dom in self.domain.rows:
            self.sync_dom_to_gcal(dom)

    def sync_dom_to_gcal(self, dom: editors.PageRow):
        gcal_link = dom.get_tag(self.Tgcal_link, '')
        gcal_id = dom.get_tag(self.Tgcal_id, '')
        synced = dom.read_tag(self.Tis_synced)
        if gcal_link and synced:
            return
        elif gcal_link and not synced:
            event = self.Gcals.EventGetter(gcal_id, self.calendar_id).execute()
            if event is None or event['status'] == 'cancelled':
                self.create_gcal(dom)
            else:
                self.update_gcal(dom)
        elif not gcal_link:
            self.create_gcal(dom)
        writer = dom
        writer.write_checkbox(tag=self.Tis_synced, value=True)

    def update_gcal(self, dom: editors.PageRow):
        dt_start, dt_end = self.get_dt_tuple(dom)
        if not dt_start:
            return
        requestor = self.Gcals.EventUpdater(
            event_id=dom.read_tag(self.Tgcal_id),
            calendar_id=self.calendar_id,
            summary=dom.title,
            start=dt_start,
            end=dt_end,
        )
        requestor.execute()

    def create_gcal(self, dom: editors.PageRow):
        dt_start, dt_end = self.get_dt_tuple(dom)
        if not dt_start:
            return
        requestor = self.Gcals.EventCreator(
            calendar_id=self.calendar_id,
            summary=dom.title,
            start=dt_start,
            end=dt_end,
        )
        event = requestor.execute()
        dom.write_text(tag=self.Tgcal_id, value=event['id'])
        dom.write_url(tag=self.Tgcal_link, value=event['htmlLink'])

    def get_dt_tuple(self, dom: editors.PageRow):
        date_start, date_end = self.get_date_vals(dom)
        time_val = self.get_time_vals(dom)
        if not date_start:
            return None, None
        if len(time_val) == 2:
            time_start, time_end = time_val
            dt_start = dt.datetime.combine(date_start, time_start).astimezone()
            dt_end = dt.datetime.combine(date_end, time_end).astimezone()
        elif len(time_val) == 1:
            time_start = time_val[0]
            dt_start = dt.datetime.combine(date_start, time_start).astimezone()
            if date_start == date_end:
                dt_end = dt_start + dt.timedelta(minutes=self.default_event_duration)
                dt_end = dt_end.astimezone()
            else:
                dt_end = dt.datetime.combine(date_end, time_start).astimezone()
        else:
            dt_start = date_start
            dt_end = date_end + dt.timedelta(days=1)
        return dt_start, dt_end

    def get_date_vals(self, dom: editors.PageRow):
        tar_ids = dom.read_tag(self.T_tar)
        date_min: Optional[dt.date] = None
        date_max: Optional[dt.date] = None
        for tar_id in tar_ids:
            tar = self.target.rows.fetch_page(tar_id)
            date_format: DateObject = tar.read_tag(self.Ttars_date)
            date_val = date_format.start_date
            if date_min is None or date_min > date_val:
                date_min = date_val
            if date_max is None or date_max < date_val:
                date_max = date_val
        return date_min, date_max

    def get_time_vals(self, dom: editors.PageRow) -> list[dt.time]:
        if timestr := dom.read_tag(self.Ttimestr):
            return TimeStringHandler(timestr).time_val
        return []
