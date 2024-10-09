from abc import ABCMeta
from collections.abc import Callable
from dataclasses import asdict, astuple, dataclass
from datetime import datetime, timedelta, timezone
from ratelimit import sleep_and_retry, limits
from typing import Any, Final, Literal, overload, Self
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
if platform.system() == "Windows":
    import tzdata

__all__ = ["TramTrackerService"]

EPOCH: Final = datetime(1970, 1, 1, tzinfo=timezone.utc)
"""datetime representation of the Unix epoch"""
TIMESTAMP_PATTERN: Final = re.compile(r"/Date\((?P<timestamp>[0-9]+)[+-][0-9]{4}\)/")
"""Regular expression for the response value of timestamps from the data service"""
TZ_MELBOURNE: Final = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""

_logger: Final = logging.getLogger("ptv-timetable.tramtracker")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


class TramTrackerError(OSError):
    """Raised when the TramTracker data service returns an error."""

    def __init__(self: Self, message: str, *args: object) -> None:
        """
        Constructs a new exception instance with the specified error message. This is used to raise an exception when the TramTracker data service responds with an error.

        :param message: Error message to display
        :param args: Any other positional-only arguments to pass to the constructor of the parent class
        :return: ``None``
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
        """Converts this ``TramTrackerData`` dataclass instance to a dict that maps its field names to their corresponding values, recursing into any dataclasses, dicts, lists and tuples and doing a ``copy.deepcopy()`` of everything else. The result can be customised by providing a ``dict_factory`` function.

        This is a convenient shorthand for ``dataclasses.asdict(self)``.

        :param dict_factory: If specified, dict creation will be customised with this function (including for nested dataclasses)
        :return: The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``
        """
        return asdict(self) if dict_factory is None else asdict(self, dict_factory=dict_factory)

    @overload
    def as_tuple(self: Self, *, tuple_factory: None = None) -> tuple[Any, ...]:
        ...

    @overload
    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T]) -> _T:
        ...

    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T] | None = None) -> tuple[Any, ...] | _T:
        """Converts this ``TramTrackerData`` dataclass instance to a tuple of its fields' values, recursing into any dataclasses, dicts, lists and tuples and doing a ``copy.deepcopy()`` of everything else. The result can be customised by providing a ``tuple_factory`` function.

        This is a convenient shorthand for ``dataclasses.astuple(self)``.

        :param tuple_factory: If specified, dict creation will be customised with this function (including for nested dataclasses)
        :return: The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``
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


class TramTrackerService(object):
    """Interface class with the TramTracker data service. Based on https://tramtracker.com.au/js/dataService.js."""

    def __init__[**_P, _R](self: Self, *, calls: int = 1, period: float = 10, ratelimit_handler: Callable[[Callable[_P, _R]], Callable[_P, _R]] = sleep_and_retry) -> None:
        """Initialises a new TramTrackerService instance.

        :param calls: Maximum number of calls that can be made to the service within the specified ``period``
        :param period: Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :param ratelimit_handler: Function decorator that handles ``ratelimit.exception.RateLimitException`` without re-raising it; defaults to ``ratelimit.decorators.sleep_and_retry``. A custom handler should match the specified signature, otherwise the program's behaviour is undefined (there is no runtime checking of the suitability of the handler)
        :return: ``None``
        """

        self._get: Callable[..., requests.models.Response] = ratelimit_handler(limits(calls, period)(requests.get))
        """requests.get() function but rate-limited"""

        _logger.info("TramTrackerService instance created")
        return

    def __del__(self: Self) -> None:
        """Logs the prospective deletion of an instance into the module logger once there are no more references to it in the program.

        Note that Python does not guarantee that this will be called for any instance.

        :return: ``None``
        """

        _logger.info("TramTrackerService instance deleted")
        return

    def call(self: Self, request: str) -> list[dict[str, str | int | float | bool | dict[str, str | int | list[str]] | None]] | dict[str, str | int | float | bool | None]:
        """Requests data from the TramTracker service and returns the response.

        :param request: The request, which is appended to the base URL of the service
        :return: A ``list`` or ``dict`` of the response data, depending on the request
        """

        url = f"http://tramtracker.com.au/Controllers{request}"
        _logger.debug("Requesting from: " + url)
        r: requests.models.Response = self._get(url)
        try:
            r.raise_for_status()
        except Exception:
            _logger.error("", exc_info=True)
            raise
        result = r.json()
        _logger.debug("Response: " + str(result))

        try:
            if ("HasError" in result and result["HasError"]) or ("hasError" in result and result["hasError"]):
                raise TramTrackerError(result["ResponseString"] if "ResponseString" in result else result["errorMessage"])
            assert ("ResponseObject" in result and result["ResponseObject"] is not None) or ("responseObject" in result and result["responseObject"] is not None)
        except Exception:
            _logger.error("", exc_info=True)
            raise

        return result["ResponseObject"] if "ResponseObject" in result else result["responseObject"]

    def list_destinations(self: Self) -> list[TramDestination]:
        """Returns a list of termini for each primary tram route on the network.

        :return: A list detailing each route terminus
        """

        response = self.call("/GetAllRoutes.ashx")
        return [TramDestination(route_id=element["InternalRouteNo"],
                                route_number=element["AlphaNumericRouteNo"] if element["AlphaNumericRouteNo"] is not None else str(element["RouteNo"]),
                                up_direction=element["IsUpDirection"],
                                destination=element["Destination"],
                                has_low_floor_trams=element["HasLowFloor"]
                                ) for element in response]

    def list_stops(self: Self, route_id: int, up_direction: bool) -> list[TramStop]:
        """Returns a list of stops on the specified route and direction of travel.

        :param route_id: The route identifier, as returned by ``list_destinations()``
        :param up_direction: Set to ``True`` to get stops in the "up" direction or ``False`` to get stops in the "down" direction, as described in ``list_destinations()``
        :return: A list of stops on the route
        """

        response = self.call(f"/GetStopsByRouteAndDirection.ashx?r={route_id}&u={"true" if up_direction else "false"}")
        return [TramStop(stop_id=element["StopNo"] if element["StopNo"] != 0 else None,
                         stop_name=element["Description"],
                         stop_number=element["FlagStopNo"],
                         stop_name_and_number=element["StopName"],
                         locality=element["Suburb"],
                         location=(element["Latitude"], element["Longitude"]) if element["Latitude"] != 0.0 and element["Longitude"] != 0.0 else None,
                         route_id=element["RouteNo"] if element["RouteNo"] != 0 else None,
                         destination=element["Destination"],
                         distance_to_location=element["DistanceToLocation"] if element["DistanceToLocation"] != 0.0 else None,
                         city_direction=element["CityDirection"]
                         ) for element in response]

    def get_stop(self: Self, stop_id: int) -> TramStop:
        """Returns information about the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return: The stop details
        """

        response = self.call(f"/GetStopInformation.ashx?s={stop_id}")
        return TramStop(stop_id=response["StopNo"] if response["StopNo"] != 0 else None,
                        stop_name=response["StopName"],
                        stop_number=response["FlagStopNo"],
                        stop_name_and_number=None,
                        locality=response["Suburb"],
                        location=(response["Latitude"], response["Longitude"]) if response["Latitude"] != 0.0 and response["Longitude"] != 0.0 else None,
                        route_id=response["RouteNo"] if response["RouteNo"] != 0 else None,
                        destination=response["Destination"],
                        distance_to_location=response["DistanceToLocation"] if response["DistanceToLocation"] != 0.0 else None,
                        city_direction=response["CityDirection"]
                        )

    def list_routes_for_stop(self: Self, stop_id: int) -> list[str]:
        """Returns a list of route numbers for the primary routes that serve the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return: A list of route numbers
        """

        response = self.call(f"/GetPassingRoutes.ashx?s={stop_id}")
        return [element["RouteNo"] for element in response]

    def next_trams(self: Self, stop_id: int, route_id: int | None = None, low_floor_tram: bool = False, as_of: datetime = datetime.now(tz=ZoneInfo("Australia/Melbourne"))) -> list[TramDeparture]:
        """Returns the details and times of the next trams to depart from the specified stop. The number of results returned can vary, but is usually three entries per destination.

        :param stop_id: The TramTracker code of the stop
        :param route_id: If specified, return next trams for the specified route identifier
        :param low_floor_tram: If set to ``True``, only departures with low-floor trams will be returned
        :param as_of: The time from which to get departures; defaults to current system time
        :return: A list of departures from the stop
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        as_of = as_of.astimezone(TZ_MELBOURNE)
        timestamp = round((as_of - EPOCH) / timedelta(milliseconds=1))
        response = self.call(f"/GetNextPredictionsForStop.ashx?stopNo={stop_id}&routeNo={route_id if route_id is not None else 0}&isLowFloor={"true" if low_floor_tram else "false"}&ts={timestamp}")
        return [TramDeparture(stop_id=stop_id,
                              trip_id=element["TripID"],
                              route_id=element["InternalRouteNo"],
                              route_number=element["HeadBoardRouteNo"],
                              primary_route_number=element["RouteNo"],
                              vehicle_id=element["VehicleNo"] if element["VehicleNo"] != 0 else None,
                              vehicle_class=element["TramClass"] if element["TramClass"] != "" else None,
                              destination=element["Destination"],
                              tt_available=element["IsTTAvailable"],
                              low_floor_tram=element["IsLowFloorTram"],
                              air_conditioned=element["AirConditioned"],
                              display_ac_icon=element["DisplayAC"],
                              has_disruption=element["HasDisruption"],
                              disruptions=element["DisruptionMessage"]["Messages"],
                              has_special_event=element["HasSpecialEvent"],
                              special_event_message=element["SpecialEventMessage"] if element["SpecialEventMessage"] != "" else None,
                              has_planned_occupation=element["HasPlannedOccupation"],
                              planned_occupation_message=element["PlannedOccupationMessage"] if element["PlannedOccupationMessage"] != "" else None,
                              estimated_departure=(EPOCH + timedelta(milliseconds=int(TIMESTAMP_PATTERN.fullmatch(element["PredictedArrivalDateTime"]).group("timestamp")))).astimezone(TZ_MELBOURNE)
                              ) for element in response]

    def get_route_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the colour of the specified route as printed on public information paraphernalia.

        :param route_id: The route identifier
        :param as_of: If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return: A hexadecimal code representing the route colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = self.call(f"/GetRouteColour.ashx?routeNo={route_id}&ts={timestamp}")
        return "#" + response["Colour"].lower()

    def get_route_text_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the text font colour on public information paraphernalia if it was written on a background with the route's colour (e.g. the route iconography).

        :param route_id: The route identifier
        :param as_of: If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return: A hexadecimal code representing the text colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = self.call(f"/GetRouteTextColour.ashx?routeNo={route_id}&ts={timestamp}")
        return "#" + response["Colour"].lower()
