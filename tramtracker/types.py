from abc import ABCMeta
from collections.abc import Callable
from dataclasses import dataclass, asdict, astuple
from datetime import datetime, timezone
from typing import Any, Final, Literal, overload, Self
from zoneinfo import ZoneInfo
import platform
import re
if platform.system() == "Windows":
    import tzdata

__all__ = ["EPOCH", "TIMESTAMP_PATTERN", "TZ_MELBOURNE", "TramTrackerError", "TramTrackerData", "TramDeparture", "TramDestination", "TramStop"]

EPOCH: Final = datetime(1970, 1, 1, tzinfo=timezone.utc)
"""datetime representation of the Unix epoch"""
TIMESTAMP_PATTERN: Final = re.compile(r"/Date\((?P<timestamp>[0-9]+)[+-][0-9]{4}\)/")
"""Regular expression for the response value of timestamps from the data service"""
TZ_MELBOURNE: Final = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""


class TramTrackerError(OSError):
    """Raised when the TramTracker data service returns an error."""

    def __init__(self: Self, message: str, *args: object) -> None:
        """Constructs a new exception instance with the specified error message. This is used to raise an exception when the TramTracker data service responds with an error.

        :param message: Error message to display
        :param args:    Any other positional-only arguments to pass to the constructor of the parent class
        :return:        ``None``
        """

        self.message = message
        """Error message sent by the server"""

        super().__init__(message, *args)
        return


@dataclass(kw_only=True, slots=True)
class TramTrackerData(object, metaclass=ABCMeta):
    """Base class for API response types."""

    @overload
    def as_dict(self: Self, *, dict_factory: None = None) -> dict[str, Any]:
        ...

    @overload
    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, Any]]], _T]) -> _T:
        ...

    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, Any]]], _T] | None = None) -> _T | dict[str, Any]:
        """Converts this :class:`TramTrackerData` dataclass instance to a dict that maps its field names to their corresponding values, recursing into any dataclasses, dicts, lists and tuples and doing a :func:`~copy.deepcopy()` of everything else. The result can be customised by providing a ``dict_factory`` function.

        This is a convenient shorthand for :func:`dataclasses.asdict(self) <dataclasses.asdict>`.

        :param dict_factory: If specified, dict creation will be customised with this function (including for nested dataclasses)
        :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``

        .. versionadded:: 0.2.1
        """
        return asdict(self) if dict_factory is None else asdict(self, dict_factory=dict_factory)

    @overload
    def as_tuple(self: Self, *, tuple_factory: None = None) -> tuple[Any, ...]:
        ...

    @overload
    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T]) -> _T:
        ...

    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T] | None = None) -> tuple[Any, ...] | _T:
        """Converts this :class:`TramTrackerData` dataclass instance to a tuple of its fields' values, recursing into any dataclasses, dicts, lists and tuples and doing a :func:`copy.deepcopy()` of everything else. The result can be customised by providing a ``tuple_factory`` function.

        This is a convenient shorthand for :func:`dataclasses.astuple(self) <dataclasses.astuple>`.

        :param tuple_factory: If specified, tuple creation will be customised with this function (including for nested dataclasses)
        :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``

        .. versionadded:: 0.2.1
        """
        return astuple(self) if tuple_factory is None else astuple(self, tuple_factory=tuple_factory)


@dataclass(kw_only=True, slots=True)
class TramDeparture(TramTrackerData):
    """Represents a tram departure from a particular stop."""

    stop_id: int
    """TramTracker code of the stop of this departure"""
    trip_id: int | None
    """Trip identifier; currently unused"""
    route_id: int
    """Route identifier for this departure"""
    route_number: str
    """Public-facing route number for this departure"""
    primary_route_number: str
    """Route number of the main route that this departure belongs to"""
    vehicle_id: int | None
    """Identifier of the tram operating this service, as printed on and inside the vehicle; None if information is not currently available"""
    vehicle_class: Literal["W", "Z3", "A1", "A2", "B2", "C1", "C2", "D1", "D2", "E", "G"] | None
    """Class/model of the tram operating this service; None if information is not currently available"""
    destination: str
    """Destination of this service"""
    tt_available: bool
    """Whether real time data is available for this departure"""
    low_floor_tram: bool
    """Whether this tram is a low-floor tram"""
    air_conditioned: bool
    """Whether this tram has air conditioning"""
    display_ac_icon: bool
    """Whether the air conditioning icon is displayed on passenger information displays for this service"""
    has_disruption: bool
    """Whether a disruption is affecting this service"""
    disruptions: list[str]
    """Descriptions of the disruptions affecting this service"""
    has_special_event: bool
    """Whether a special event is affecting or will affect this route"""
    special_event_message: str | None
    """Description of the special event"""
    has_planned_occupation: bool
    """Whether planned service changes are affecting/will affect this route"""
    planned_occupation_message: str | None
    """Description of the planned service changes"""
    estimated_departure: datetime
    """Estimated real-time departure time of this service from this stop"""


@dataclass(kw_only=True, slots=True)
class TramDestination(TramTrackerData):
    """Represents a destination of a tram route."""

    route_id: int
    """Route identifier for this destination"""
    route_number: str
    """Public-facing route number for this destination"""
    up_direction: bool
    """Whether this destination is in the "up" direction"""
    destination: str
    """Name of this destination"""
    has_low_floor_trams: bool
    """Whether low-floor trams service this route (either fully or partially)"""


@dataclass(kw_only=True, slots=True)
class TramStop(TramTrackerData):
    """Represents a tram stop."""

    stop_id: int | None
    """This stop's TramTracker code"""
    stop_name: str
    """Name of this stop"""
    stop_number: str | None
    """Stop number of this stop as printed on the signage"""
    stop_name_and_number: str | None
    """Stop name and number combined in one string"""
    locality: str | None
    """Locality (suburb/town) this stop is in"""
    location: tuple[float, float] | None
    """Currently unused; latitude-longitude coordinates of this stop"""
    route_id: None
    """Currently unused"""
    destination: None
    """Currently unused"""
    distance_to_location: float | None
    """Currently unused"""
    city_direction: str | None
    """Descriptor of the direction of travel for this stop (e.g. towards or away from city)"""
