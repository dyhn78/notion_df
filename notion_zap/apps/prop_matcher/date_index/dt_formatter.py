import datetime as dt
import re
from typing import Union, Optional


class TimeStringHandler:
    PATTERNS = [
        # HH:MM type, exclude {digits, ':'} on both sides
        PT0 := re.compile(r"(?<![\d:])(\d{2}):(\d{2})(?![\d:])"),

        # HH:M type, exclude {digits, ':'} on both sides
        PT1 := re.compile(r"(?<![\d:])(\d{2}):(\d)(?![\d:])"),

        # HH-HH, HH~HH or HH/HH type, exclude {digits, ':', '-'} on both sides
        PT2 := re.compile(r"(?<![\d:-])(\d{2})[-~/](\d{2})(?![\d:-])"),

        # HH type, only allow blanks on both sides
        PT3 := re.compile(r"(?<!\S)(\d{2})(?!\S)"),
    ]

    SUB_COUNT = [2, 2, 1, 2]

    def __init__(self, timestr: str):
        self.timestr = timestr
        time_val, remnant = self._parse(timestr)
        self.time_val: list[dt.time] = time_val
        self.remnant: str = remnant.replace('-', '')

    def _cleaned_parse(self, timestr: str):
        ret, remnant = self._parse(timestr)
        ret = self._remove_end_if_earlier_than_start(ret)
        return ret, remnant

    def _parse(self, timestr: str):
        if res := self.PT0.findall(timestr):
            ret = []
            for hours, minutes in res:
                if time_val := self._construct_time(hours, minutes):
                    ret.append(time_val)
            if ret:
                return ret[:2], self.PT0.sub('', self.timestr, 2)
        if res := self.PT1.findall(timestr):
            ret = []
            for hours, min10 in res:
                if time_val := self._construct_time(hours, min10 * 10):
                    ret.append(time_val)
            if ret:
                return ret[:2], self.PT1.sub('', self.timestr, 2)
        if res := self.PT2.findall(timestr):
            for hours1, hours2 in res:
                if ret := [self._construct_time(hours1, 0),
                           self._construct_time(hours2, 0)]:
                    return ret, self.PT2.sub('', self.timestr, 1)
        if res := self.PT3.findall(timestr):
            ret = []
            for hours in res:
                if time_val := self._construct_time(hours, 0):
                    ret.append(time_val)
            if ret:
                return ret[:2], self.PT3.sub('', self.timestr, 2)
        return [], self.timestr

    def replace(self, start: dt.time, end: Optional[dt.time] = None):
        if end and start != end:
            if start.minute == end.minute == 0:
                new_timestr = f"{start.strftime('%H')}-{end.strftime('%H')}"
            else:
                new_timestr = f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        else:
            new_timestr = start.strftime('%H:%M')
        if self.remnant:
            return f"{new_timestr} {self.remnant}"
        else:
            return new_timestr

    @staticmethod
    def _construct_time(hours: Union[str, int], minutes: Union[str, int]):
        try:
            return dt.time(int(hours), int(minutes))
        except ValueError:
            return None

    @staticmethod
    def _remove_end_if_earlier_than_start(ret: list[dt.time]):
        if len(ret) == 2 and ret[1] < ret[0]:
            return ret[0]
        return ret


def _construct_time(hours: Union[str, int], minutes: Union[str, int]):
    try:
        return dt.time(int(hours), int(minutes))
    except ValueError:
        return None


def parse_timestr(timestr: str) -> list[dt.time]:
    if res := re.findall(r"(?<![\d:])(\d{2}):(\d{2})(?![\d:])", timestr):
        # HH:MM type, exclude {digits, ':'} on both sides
        ret = []
        for hours, minutes in res:
            if time_val := _construct_time(hours, minutes):
                ret.append(time_val)
        if ret:
            return ret[:2]
    if res := re.findall(r"(?<![\d:])(\d{2}):(\d)(?![\d:])", timestr):
        # HH:M type, exclude {digits, ':'} on both sides
        ret = []
        for hours, min10 in res:
            if time_val := _construct_time(hours, min10 * 10):
                ret.append(time_val)
        if ret:
            return ret[:2]
    if res := re.findall(r"(?<![\d:-])(\d{2})-(\d{2})(?![\d:-])", timestr):
        # HH-HH type, exclude {digits, ':', '-'} on both sides
        for hours1, hours2 in res:
            if ret := [_construct_time(hours1, 0), _construct_time(hours2, 0)]:
                return ret
    if res := re.findall(r"(?<!\S)(\d{2})(?!\S)", timestr):
        # HH type, only allow blanks on both sides
        ret = []
        for hours in res:
            if time_val := _construct_time(hours, 0):
                ret.append(time_val)
        if ret:
            return ret[:2]
    return []
