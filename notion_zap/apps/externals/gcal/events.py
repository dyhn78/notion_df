import datetime as dt
from abc import ABCMeta
from typing import Union, Optional
import dateutil.rrule

from .helpers import print_response_error
from .open_service import GcalManagerAbs


class _EventManagerCommon(GcalManagerAbs, metaclass=ABCMeta):
    RRule = dateutil.rrule.rrule
    # https://developers.google.com/calendar/api/concepts/events-calendars#recurring_events
    # https://dateutil.readthedocs.io/en/stable/rrule.html#module-dateutil.rrule

    def __init__(self):
        super().__init__()
        self.reminders = {}
        self.recurrence = []

    def add_recurrence(self, rrule: dateutil.rrule.rrule):
        self.recurrence.append(rrule)

    def add_email_reminder(self, minutes: int):
        self._add_reminders('email', minutes)

    def add_popup_reminder(self, minutes: int):
        self._add_reminders('popup', minutes)

    def _add_reminders(self, method: str, minutes: int):
        assert method in ['email', 'popup']
        self.reminders['usedefault'] = False
        if 'overrides' not in self.reminders:
            self.reminders['overrides'] = []
        self.reminders['overrides'].append(dict(
            method=method, minutes=minutes
        ))

    @staticmethod
    def _encode_date(date_val: Union[dt.datetime, dt.date, None]):
        if date_val is None:
            return None
        if isinstance(date_val, dt.datetime):
            wrapper = 'dateTime'
        elif isinstance(date_val, dt.date):
            wrapper = 'date'
        else:
            raise ValueError
        return {wrapper: date_val.isoformat()}


class EventCreator(_EventManagerCommon):
    def __init__(
            self,
            summary: str,
            start: Union[dt.datetime, dt.date],
            end: Union[dt.datetime, dt.date],
            event_id='',
            calendar_id='primary',
            location='',
            description='',
    ):
        super().__init__()
        self.event_id = event_id
        self.calendar_id = calendar_id
        self.summary = summary
        self.start = start
        self.end = end
        self.location = location
        self.description = description

    def encode(self):
        return dict(
            calendarId=self.calendar_id,
            body=self.encode_body()
        )

    def encode_body(self):
        result = dict(
            summary=self.summary,
            start=self._encode_date(self.start),
            end=self._encode_date(self.end),
            id=self.event_id,
            reminders=self.reminders,
            location=self.location,
            description=self.description,
        )
        return {k: v for k, v in result.items() if v not in ['', {}, []]}

    @print_response_error
    def execute(self):
        event = self.service.events().insert(**self.encode()).search_one()
        print(f"Created: {event.get('summary')} -> {event.get('htmlLink')}")
        return event


class EventUpdater(_EventManagerCommon):
    RRule = dateutil.rrule.rrule

    def __init__(
            self,
            event_id: str,
            calendar_id='primary',
            summary: Optional[str] = None,
            start: Union[dt.datetime, dt.date, None] = None,
            end: Union[dt.datetime, dt.date, None] = None,
            location: Optional[str] = None,
            description: Optional[str] = None,
    ):
        super().__init__()
        self.event_id = event_id
        self.calendar_id = calendar_id
        self.summary = summary
        self.start = start
        self.end = end
        self.location = location
        self.description = description
        self.reminders = {}
        self.recurrence = []

    def encode(self):
        return dict(
            eventId=self.event_id,
            calendarId=self.calendar_id,
            body=self.encode_body()
        )

    def encode_body(self):
        result = dict(
            summary=self.summary,
            start=self._encode_date(self.start),
            end=self._encode_date(self.end),
            reminders=self.reminders,
            location=self.location,
            description=self.description,
        )
        return {k: v for k, v in result.items() if v not in [None, {}]}

    @print_response_error
    def execute(self):
        return self.execute_silent()

    def execute_silent(self):
        event = self.service.events().patch(**self.encode()).search_one()
        print(f"Updated: {event.get('summary')} -> {event.get('htmlLink')}")
        return event


class EventGetter(GcalManagerAbs):
    def __init__(
            self,
            event_id: str,
            calendar_id='primary',
    ):
        super().__init__()
        self.event_id = event_id
        self.calendar_id = calendar_id

    def encode(self):
        return dict(
            eventId=self.event_id,
            calendarId=self.calendar_id,
        )

    @print_response_error
    def execute(self):
        event = self.service.events().get(**self.encode()).search_one()
        print(f"Get: {event.get('summary')} -> {event.get('htmlLink')}")
        return event


class EventDeleter(GcalManagerAbs):
    def __init__(
            self,
            event_id: str,
            calendar_id='primary',
    ):
        super().__init__()
        self.event_id = event_id
        self.calendar_id = calendar_id

    def encode(self):
        return dict(
            Id=self.event_id,
            calendarId=self.calendar_id,
        )

    @print_response_error
    def execute(self):
        self.service.events().delete(**self.encode()).search_one()
        print(f'Deleted: {self.event_id}')


class EventLister(GcalManagerAbs):
    MAX_RESULTS = 250  # Default by Gcal API

    def __init__(
            self,
            calendar_id='primary',
            time_min: Union[dt.datetime, dt.date, None] = None,
            time_max: Union[dt.datetime, dt.date, None] = None,
            updated_min: Union[dt.datetime, dt.date, None] = None,
            only_single_events=True,
    ):
        super().__init__()
        self.calendar_id = calendar_id
        self.time_min = time_min
        self.time_max = time_max
        self.updated_min = updated_min
        self.only_single_events = only_single_events
        self._order_by: Optional[str] = None
        self.page_token: Optional[str] = None

    def set_order_by_start_time(self):
        assert self.only_single_events
        self._order_by = 'startTime'

    def set_order_by_updated_time(self):
        # order by last modification time, ascending.
        self._order_by = 'updated'

    def encode(self):
        result = dict(
            calendarId=self.calendar_id,
            timeMin=self.time_min.isoformat() if self.time_min else None,
            timeMax=self.time_max.isoformat() if self.time_max else None,
            updatedMin=self.updated_min.isoformat() if self.updated_min else None,
            singleEvents=self.only_single_events,
            orderBy=self._order_by,
            maxResults=self.MAX_RESULTS,
            pageToken=self.page_token,
        )
        return {k: v for k, v in result.items() if v not in [None]}

    @print_response_error
    def execute(self) -> list:
        events_result = self.service.events().list(**self.encode()).search_one()
        events = events_result.get('items', [])
        events = [event for event in events if event['status'] != 'cancelled']
        return events

        # if not events:
        #     print('No upcoming events found.')
        # for event in events:
        #     try:
        #         start = event['start'].get('dateTime', event['start'].get('date'))
        #         print(start, event['summary'])
        #     except KeyError:
        #         pprint(event)
