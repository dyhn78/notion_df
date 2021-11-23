import datetime as dt
from typing import Union, Optional

from notion_zap.apps.externals.gcal import GcalEditor


class GcalEventCreator(GcalEditor):
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
        self.reminders = {}

    def add_reminders(self, method: str, minutes: int):
        assert method in ['email', 'popup']
        self.reminders['usedefault'] = False
        if 'overrides' not in self.reminders:
            self.reminders['overrides'] = []
        self.reminders['overrides'].append(dict(
            method=method, minutes=minutes
        ))

    def encode(self):
        return dict(
            calendarId=self.calendar_id,
            body=self.encode_body()
        )

    def encode_body(self):
        result = dict(
            summary=self.summary,
            start=self.start.isoformat(),
            end=self.end.isoformat(),
            id=self.event_id,
            reminders=self.reminders,
            location=self.location,
            description=self.description,
        )
        return {k: v for k, v in result if v not in ['', {}]}

    def execute(self):
        event = self.service.events().insert(self.encode()).execute()
        print('Event created: %s' % (event.get('htmlLink')))


class GcalEventUpdater(GcalEditor):
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

    def add_reminders(self, method: str, minutes: int):
        assert method in ['email', 'popup']
        self.reminders['usedefault'] = False
        if 'overrides' not in self.reminders:
            self.reminders['overrides'] = []
        self.reminders['overrides'].append(dict(
            method=method, minutes=minutes
        ))

    def encode(self):
        return dict(
            calendarId=self.calendar_id,
            body=self.encode_body()
        )

    def encode_body(self):
        result = dict(
            summary=self.summary,
            start=self.start.isoformat(),
            end=self.end.isoformat(),
            id=self.event_id,
            reminders=self.reminders,
            location=self.location,
            description=self.description,
        )
        return {k: v for k, v in result if v not in ['', {}]}

    def execute(self):
        event = self.service.events().insert(self.encode()).execute()
        print('Event created: %s' % (event.get('htmlLink')))
