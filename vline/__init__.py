from collections import defaultdict
from dataclasses import asdict, astuple, dataclass
from datetime import datetime, time, timedelta
from html.parser import HTMLParser
from typing import Any, Callable, Final, overload, override, Self, Literal
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
from ratelimit import limits
from ratelimit.decorators import sleep_and_retry

if platform.system() == "Windows":
    import tzdata

__all__ = ["next_services"]

type PlatformNumber = Literal["1", "2", "2A", "2B", "3", "3A", "3B", "4", "4A", "4B", "5", "5A", "5B", "6", "6A", "6B", "7", "7A", "7B", "8", "8A", "8B", "8S", "15", "15A", "15B", "16", "16A", "16B"]

TZ_MELBOURNE: Final = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""

_logger: Final = logging.getLogger("ptv-timetable.vline")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())

@dataclass(kw_only=True, slots=True)
class Departure(object):
    """Represents a V/Line departure from Southern Cross station."""

    id: str
    """Service identifier on the V/Line website"""
    scheduled_departure: datetime
    """Scheduled departure time of the service"""
    destination: str
    """Destination of the service"""
    platform: PlatformNumber
    """Platform number the service is departing from"""
    departing_in: timedelta
    """Estimated time (in minutes) before the service departs; timedelta(minutes=0) indicates now"""

    @overload
    def as_dict(self: Self, *, dict_factory: None = None) -> dict[str, str | datetime | PlatformNumber | timedelta]:
        ...

    @overload
    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, str | datetime | PlatformNumber | timedelta]]], _T]) -> _T:
        ...

    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, str | datetime | PlatformNumber | timedelta]]], _T] | None = None) -> _T | dict[str, Any]:
        """Returns this instance's fields as a :class:`dict`. The result can be customised by providing a ``dict_factory`` function.

        This is a convenient shorthand for ``dataclasses.asdict(self)``.

        :param dict_factory: If specified, dict creation will be customised with this function
        :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``
        """
        return asdict(self) if dict_factory is None else asdict(self, dict_factory=dict_factory)

    @overload
    def as_tuple(self: Self, *, tuple_factory: None = None) -> tuple[Any, ...]:
        ...

    @overload
    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[str | datetime | PlatformNumber | timedelta]], _T]) -> _T:
        ...

    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[str | datetime | PlatformNumber | timedelta]], _T] | None = None) -> tuple[Any, ...] | _T:
        """Returns this instance's fields' values as a :class:`tuple`, in order of declaration. The result can be customised by providing a ``tuple_factory`` function.

        This is a convenient shorthand for ``dataclasses.astuple(self)``.

        :param tuple_factory: If specified, tuple creation will be customised with this function
        :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``
        """
        return astuple(self) if tuple_factory is None else astuple(self, tuple_factory=tuple_factory)


@dataclass(kw_only=True, slots=True)
class Arrival(object):
    """Represents a V/Line arrival at Southern Cross station"""

    scheduled_arrival: datetime
    """Scheduled arrival time of the service"""
    origin: str
    """Origin of the service"""
    platform: PlatformNumber
    """Platform number the service is expected to arrive at"""
    arriving_in: timedelta
    """Estimated time (in minutes) before the service arrives; timedelta(minutes=0) indicates now"""

    @overload
    def as_dict(self: Self, *, dict_factory: None = None) -> dict[str, str | datetime | PlatformNumber | timedelta]:
        ...

    @overload
    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, str | datetime | PlatformNumber | timedelta]]], _T]) -> _T:
        ...

    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, str | datetime | PlatformNumber | timedelta]]], _T] | None = None) -> _T | dict[str, Any]:
        """Returns this instance's fields as a :class:`dict`. The result can be customised by providing a ``dict_factory`` function.

        This is a convenient shorthand for ``dataclasses.asdict(self)``.

        :param dict_factory: If specified, dict creation will be customised with this function
        :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``
        """
        return asdict(self) if dict_factory is None else asdict(self, dict_factory=dict_factory)

    @overload
    def as_tuple(self: Self, *, tuple_factory: None = None) -> tuple[Any, ...]:
        ...

    @overload
    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[str | datetime | PlatformNumber | timedelta]], _T]) -> _T:
        ...

    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[str | datetime | PlatformNumber | timedelta]], _T] | None = None) -> tuple[Any, ...] | _T:
        """Returns this instance's fields' values as a :class:`tuple`, in order of declaration. The result can be customised by providing a ``tuple_factory`` function.

        This is a convenient shorthand for ``dataclasses.astuple(self)``.

        :param tuple_factory: If specified, tuple creation will be customised with this function
        :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``
        """
        return astuple(self) if tuple_factory is None else astuple(self, tuple_factory=tuple_factory)


class _ServiceInfoScraper(HTMLParser):
    """Scrapes real-time platform information data from the V/Line website."""

    pattern_attrs = re.compile(r"HandleMouseClick\(event,\s*'Melbourne, Southern Cross',\s*'(?P<scheduled_departure>[0-2][0-9]:[0-5][0-9])',\s*'(?P<destination>[\w ]+) Station:?[\w\s]*',\s*'(?P<platform>1?[0-9]+[ABS]?)',\s*'(?P<id>[0-9]*)'\);")
    pattern_dep = re.compile(r"Departing (?:in (\d+) min|(now))")
    pattern_ori = re.compile(r"(?P<origin>[\w ]+) Station:?[\w\s]*")
    pattern_plat = re.compile(r"Platform (?P<platform>1?[0-9]+[ABS]?)")
    pattern_arr = re.compile(r"Arriving(?: in (\d+) min)?")

    def __init__(self: Self) -> None:
        """Constructs a new instance and request the required information from the V/Line website.

        :return: ``None``
        """
        super().__init__()
        self.departures: list[Departure] = []
        """List of V/Line departures from Southern Cross station"""
        self.arrivals: list[Arrival] = []
        """List of V/Line arrivals into Southern Cross station"""
        self._current: dict[str, Any] | None = None
        self._stack: list[list[str]] = []

        self.as_at: Final[datetime] = datetime.now(tz=TZ_MELBOURNE)
        """Time of information request"""
        r = requests.get("https://www.vline.com.au")
        r.raise_for_status()
        self.feed(r.text)
        return

    @override
    def handle_starttag(self: Self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Method used by :class:`html.HTMLParser` to process HTML data.
        """
        if tag == "div":
            attrs: defaultdict[str, str | None] = defaultdict(lambda: None, attrs)
            if attrs["class"] is not None and len(self._stack) == 0:
                html_class = attrs["class"].split(" ")
                if "depatureDesktopBrowser" in html_class:
                    self._stack.append(html_class)
                    assert attrs["onclick"]
                    self._current = self.pattern_attrs.search(attrs["onclick"]).groupdict()
                elif "arrivalDesktopBrowser" in html_class:
                    self._stack.append(html_class)
                    self._current = {}
            elif len(self._stack) > 0:
                self._stack.append(attrs["class"].split(" ") if attrs["class"] is not None else [])
        return

    @override
    def handle_data(self: Self, data: str) -> None:
        """Method used by :class:`html.HTMLParser` to process HTML data.
        """
        if self._current is not None and len(self._stack) > 0:
            # Departing services
            if "timeTableCell" in self._stack[-1]:
                assert data.strip() == self._current["scheduled_departure"]
                h, m = self._current["scheduled_departure"].split(":")
                self._current["scheduled_departure"] = self.as_at.replace(hour=int(h), minute=int(m), second=0, microsecond=0, tzinfo=TZ_MELBOURNE)
                if self.as_at > self._current["scheduled_departure"]:  # if current time is after the scheduled service time with today's date (i.e. services after midnight)
                    self._current["scheduled_departure"] += timedelta(days=1)  # substitute date with next day
            elif "departureDestinationTableCell" in self._stack[-1]:
                assert data.strip().startswith(self._current["destination"])
            elif "departureArrivalPlatformNumberTableCell" in self._stack[-1]:
                assert data.strip().endswith(self._current["platform"])
            elif "departingArrivingTextTableCell" in self._stack[-1]:
                match = self.pattern_dep.match(data.strip())
                assert match is not None
                if match.group(2) is not None:
                    self._current["departing_in"] = timedelta()
                else:
                    self._current["departing_in"] = timedelta(minutes=int(match.group(1)))

            # Arriving services
            elif "arrivalTimeTableCell" in self._stack[-1]:
                h, m = data.strip().split(":")
                self._current["scheduled_arrival"] = time(hour=int(h), minute=int(m), second=0, microsecond=0, tzinfo=TZ_MELBOURNE)
            elif "arrivalOriginTableCell" in self._stack[-1]:
                self._current["origin"] = self.pattern_ori.search(data.strip()).group("origin")
            elif "arrivalPlatformNumberTableCell" in self._stack[-1]:
                self._current["platform"] = self.pattern_plat.search(data.strip()).group("platform")
            elif "arrivingTextTableCell" in self._stack[-1]:
                match = self.pattern_arr.search(data.strip())
                if match.group(1) is None:
                    self._current["arriving_in"] = timedelta()
                else:
                    self._current["arriving_in"] = timedelta(minutes=int(match.group(1)))
        return

    @override
    def handle_endtag(self: Self, tag: str) -> None:
        """Method used by :class:`html.HTMLParser` to process HTML data.
        """
        if len(self._stack) > 0:
            html_class = self._stack.pop()
            if "depatureDesktopBrowser" in html_class:
                self.departures.append(Departure(**self._current))
                self._current = None
                assert len(self._stack) == 0
            elif "arrivalDesktopBrowser" in html_class:
                self.arrivals.append(Arrival(**self._current))
                self._current = None
                assert len(self._stack) == 0
        return

@sleep_and_retry
@limits(calls=1, period=10)
def next_services() -> tuple[list[Departure], list[Arrival], datetime]:
    """Returns real-time information for the V/Line services departing from and arriving at Southern Cross railway station within the next 30 minutes from the time of the request.

    :return: A 3-tuple with a list of departing and arriving services, and the time of the response, respectively
    """
    s = _ServiceInfoScraper()
    return s.departures, s.arrivals, s.as_at
