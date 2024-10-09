from collections.abc import Iterable, Callable
from datetime import datetime, timezone
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from typing import cast, Final, Literal, overload, Self
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
import urllib.parse
if platform.system() == "Windows":
    import tzdata

from .types import *

__all__ = ["TimetableAPI", "METROPOLITAN_TRAIN", "METRO_TRAIN", "MET_TRAIN", "METRO", "TRAM", "BUS", "REGIONAL_TRAIN", "REG_TRAIN", "COACH", "VLINE", "EXPAND_ALL", "EXPAND_STOP", "EXPAND_ROUTE", "EXPAND_RUN", "EXPAND_DIRECTION", "EXPAND_DISRUPTION", "EXPAND_VEHICLE_DESCRIPTOR", "EXPAND_VEHICLE_POSITION", "EXPAND_NONE"]

type _Values = str | int | float | bool | datetime | _Record
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

type ExpandType = Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]
type RouteType = Literal[0, 1, 2, 3]

TZ_MELBOURNE: Final = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""
UUID_PATTERN: Final = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")
"""Regular expression for a universally unique identifier"""

METROPOLITAN_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in `route_type` parameters"""
METRO_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in `route_type` parameters"""
MET_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in `route_type` parameters"""
METRO: Literal[0] = 0
"""Metropolitan trains. For use in `route_type` parameters"""
TRAM: Literal[1] = 1
"""Metropolitan trams. For use in `route_type` parameters"""
BUS: Literal[2] = 2
"""Metropolitan & regional buses. For use in `route_type` parameters"""
REGIONAL_TRAIN: Literal[3] = 3
"""Regional trains & coaches. For use in `route_type` parameters"""
REG_TRAIN: Literal[3] = 3
"""Regional trains & coaches. For use in `route_type` parameters"""
COACH: Literal[3] = 3
"""Regional trains & coaches. For use in `route_type` parameters"""
VLINE: Literal[3] = 3
"""Regional trains & coaches. For use in `route_type` parameters"""

EXPAND_ALL: Literal["All"] = "All"
"""Return all object properties in full. For use in `expand` parameters"""
EXPAND_STOP: Literal["Stop"] = "Stop"
"""Return stop properties. For use in `expand` parameters"""
EXPAND_ROUTE: Literal["Route"] = "Route"
"""Return route properties. For use in `expand` parameters"""
EXPAND_RUN: Literal["Run"] = "Run"
"""Return run properties. For use in `expand` parameters"""
EXPAND_DIRECTION: Literal["Direction"] = "Direction"
"""Return direction properties. For use in `expand` parameters"""
EXPAND_DISRUPTION: Literal["Disruption"] = "Disruption"
"""Return disruption properties. For use in `expand` parameters"""
EXPAND_VEHICLE_DESCRIPTOR: Literal["VehicleDescriptor"] = "VehicleDescriptor"
"""Return vehicle descriptor properties. For use in `expand` parameters"""
EXPAND_VEHICLE_POSITION: Literal["VehiclePosition"] = "VehiclePosition"
"""Return vehicle position properties. For use in `expand` parameters"""
EXPAND_NONE: Literal["None"] = "None"
"""Don't return any object properties. For use in `expand` parameters"""

_logger: Final = logging.getLogger("ptv-timetable.ptv_timetable")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


class TimetableAPI(object):
    """Interface class with the PTV Timetable API."""

    def __init__[**_P, _R](self: Self, dev_id: str | int, key: str, *, calls: int = 1, period: float = 10, ratelimit_handler: Callable[[Callable[_P, _R]], Callable[_P, _R]] = sleep_and_retry) -> None:
        """Initialises a new TimetableAPI instance with the supplied credentials.

        :param dev_id: User ID
        :param key: API request signing key (a UUID)
        :param calls: Maximum number of calls that can be made to the API within the specified ``period``
        :param period: Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :param ratelimit_handler: Function decorator that handles ``ratelimit.exception.RateLimitException`` without re-raising it; defaults to ``ratelimit.decorators.sleep_and_retry``. A custom handler should match the specified signature, otherwise the program's behaviour is undefined (there is no runtime checking of the suitability of the handler)
        :return: ``None``
        """

        if type(dev_id) not in (str, int):
            raise TypeError(f"devID must be str or int, not {type(dev_id).__name__}")
        if type(key) is not str:
            raise TypeError(f"key must be str, not {type(key).__name__}")

        if UUID_PATTERN.fullmatch(key) is None:
            raise ValueError(f"key is not a UUID string: {key}")

        self._dev_id: Final[str] = str(dev_id)
        """API user ID"""
        self._key: Final[bytes] = key.encode(encoding="ascii")
        """API request signing key"""
        self._get: Callable[..., requests.models.Response] = ratelimit_handler(limits(calls, period)(requests.get))
        """requests.get() function but rate-limited"""

        _logger.info("PTVAPI instance created")
        return

    def __del__(self: Self) -> None:
        """Logs the prospective deletion of an instance into the module logger once there are no more references to it in the program.

        Note that Python does not guarantee that this will be called for any instance.

        :return: ``None``
        """

        _logger.info("PTVAPI instance deleted")
        return

    @staticmethod
    def build_arg_string(*params: tuple[str, str | int | bool | Iterable[str | int] | None] | str | int | bool | Iterable[str | int] | None, s: str = "") -> str:
        """Builds a URL argument string using the specified parameter-value pairs. Automatically expands values that are ``Iterable``. Ignores values that are ``None``.

        :param params: Tuples of (param, value) pairs, or the param and values themselves (must contain the exact number of arguments to complete the URL)
        :param s: Optionally, the string to append to
        :return: Modified URL string
        """

        i = 0
        while i < len(params):
            if isinstance(params[i], tuple):
                if isinstance(params[i][1], str) or type(params[i][1]) is int:
                    s += f"{"&" if "?" in s else "?"}{params[i][0]}={params[i][1]}"
                elif type(params[i][1]) is bool:
                    s += f"{"&" if "?" in s else "?"}{params[i][0]}={"true" if params[i][1] else "false"}"
                elif isinstance(params[i][1], Iterable):
                    for value in params[i][1]:
                        if isinstance(value, str) or type(value) is int:
                            s += f"{"&" if "?" in s else "?"}{params[i][0]}={value}"
                        else:
                            raise TypeError(f"second element of argument {i} ({params[i]}) contains values that are neither str nor int")
                elif params[i][1] is not None:
                    raise TypeError(f"second element of argument {i} ({params[i]}) must be str, int, bool or Iterable[str | int], not {type(params[i]).__name__}")
                i += 1

            elif isinstance(params[i], str):
                if i + 1 >= len(params):
                    raise ValueError(f"not enough arguments provided (missing value for {params[i]})")
                elif isinstance(params[i + 1], str) or type(params[i + 1]) is int:
                    s += f"{"&" if "?" in s else "?"}{params[i]}={params[i + 1]}"
                elif type(params[i + 1]) is bool:
                    s += f"{"&" if "?" in s else "?"}{params[i]}={"true" if params[i + 1] else "false"}"
                elif isinstance(params[i + 1], Iterable):
                    for value in params[i + 1]:
                        if isinstance(value, str) or type(value) is int:
                            s += f"{"&" if "?" in s else "?"}{params[i]}={value}"
                        else:
                            raise TypeError(f"argument {i + 1} ({params[i + 1]}) contains values that are neither str nor int")
                elif params[i + 1] is not None:
                    raise TypeError(f"argument {i + 1} ({params[i + 1]}) must be str, int, bool or Iterable[str | int], not {type(params[i + 1]).__name__}")
                i += 2

            else:
                raise TypeError(f"argument {i} ({params[i]}) is not tuple or str")

        return s

    def call(self: Self, request: str) -> dict[str, _Record | list[_Record]]:
        """Make the request to the API and format the result. This will be rate-limited based on the options provided when this instance was created.

        :param request: API request string
        :return: Result of API request as a ``dict``
        """

        url = self._encode_url(request)
        _logger.debug("Requesting from: " + url)
        r: requests.models.Response = self._get(url)
        try:
            r.raise_for_status()
        except Exception:
            _logger.error("", exc_info=True)
            raise
        result = r.json()
        _logger.debug("Response: " + str(result))
        return result

    def _encode_url(self: Self, request: str) -> str:
        """Appends the signature and base URL to the request string.

        :param request: API request string
        :return: API request URL
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self._dev_id}"
        signature = HMAC(key=self._key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

    def list_route_directions(self: Self, route_id: int) -> list[Direction]:
        """Returns the directions of travel for a particular route.

        :param route_id: The route identifier
        :return: List of directions
        """

        return [Direction.load(**item) for item in self.call(f"/v3/directions/route/{route_id}")["directions"]]

    def get_direction(self: Self, direction_id: int, route_type: RouteType | None = None) -> list[Direction]:
        """Returns the direction(s) of travel in the database with the specified identifier and route type. If ``route_type`` isn't specified, this will return directions of travel for all modes (which are likely unrelated to one another). Note that this returns a ``list`` in both cases.

        If the direction is shared by multiple routes (e.g. Flinders Street), a ``Direction`` object will be added to the ``list`` for `each` route.

        :param direction_id: The direction identifier
        :param route_type: Return the directions with the specified route type
        :return: List of directions
        """

        req = f"/v3/directions/{direction_id}" + (f"/route_type/{route_type}" if route_type is not None else "")
        return [Direction.load(**item) for item in self.call(req)["directions"]]

    def get_pattern(self: Self,
                    run_ref: str | int,
                    route_type: RouteType,
                    stop_id: int | None = None,
                    date: datetime | str | None = None,
                    include_skipped_stops: bool | None = None,
                    expand: ExpandType | Iterable[ExpandType] | None = None,
                    include_geopath: bool | None = None
                    ) -> StoppingPattern:
        """Returns the stopping pattern of the specified run of the specified route type.

        :param run_ref: The run identifier
        :param route_type: The run's travel mode identifier
        :param stop_id: Include only the stop with the specified stop ID
        :param date: Doesn't appear to have any effect on the response
        :param include_skipped_stops: Include a list of stops that are skipped by the pattern (server default is ``False``)
        :param expand: Optional data to include in the response (server default is ``EXPAND_DISRUPTION``)
        :param include_geopath: Include the pattern's path geometry (server default is ``False``)
        :return: The stopping pattern of the specified run
        """

        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = self.build_arg_string("stop_id", stop_id, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "include_skipped_stops", include_skipped_stops, "expand", expand, "include_geopath", include_geopath, s=req)

        res = self.call(req)
        return StoppingPattern.load(**res)

    def get_route(self: Self, route_id: int, include_geopath: bool | None = None, geopath_date: datetime | str | None = None) -> Route:
        """Returns the details of the route with the specified route identifier.

        :param route_id: The route identifier
        :param include_geopath: Include the route's path geometry (server default is ``False``)
        :param geopath_date: Retrieve the path geometry valid at the specified geopath_date (ISO 8601 formatted if ``str``). Defaults to current server time. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :return: Details of the specified route
        """

        if isinstance(geopath_date, str):
            geopath_date = datetime.fromisoformat(geopath_date)
        if geopath_date is not None and geopath_date.tzinfo is None:
            geopath_date = geopath_date.replace(tzinfo=TZ_MELBOURNE)

        req = self.build_arg_string("include_geopath", include_geopath, "geopath_utc", geopath_date, s=f"/v3/routes/{route_id}")
        return Route.load(**self.call(req)["route"])

    def list_routes(self: Self, route_types: Iterable[RouteType] | None = None, route_name: str | None = None) -> list[Route]:
        """Returns all routes of all (or specified) types.

        :param route_types: Return only the routes of the specified type(s)
        :param route_name: Return the routes with names containing the specified substring
        :return: A list of routes
        """

        req = self.build_arg_string("route_types", route_types, "route_name", route_name, s="/v3/routes")
        return [Route.load(**item) for item in self.call(req)["routes"]]

    def list_route_types(self: Self) -> list[dict[Literal["route_type_name", "route_type"], str | int]]:
        """Returns the names and identifiers of all route types.

        The returned dicts contain these items:
        "route_type_name" (str): Name of the route type
        "route_type" (int): Value representing the route type

        :return: A list of records containing the aforementioned fields
        """

        return cast(list[dict[Literal["route_type_name", "route_type"], str | int]], self.call("/v3/route_types")["route_types"])

    def get_run(self: Self,
                run_ref: str | int,
                route_type: RouteType | None = None,
                expand: Literal["All", "VehicleDescriptor", "VehiclePosition", "None"] | Iterable[Literal["All", "VehicleDescriptor", "VehiclePosition", "None"]] | None = None,
                date: datetime | str | None = None,
                include_geopath: bool | None = None
                ) -> list[Run]:
        """Returns a list of all runs with the specified run identifier and, optionally, the specified route type.

        :param run_ref: The run identifier
        :param route_type: Return runs of the specified type only
        :param expand: Optional data to include in the response (server default is ``EXPAND_NONE``)
        :param date: Return only data from the specified date. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :param include_geopath: Include the run's path geometry (server default is ``False``)
        :return: A list of runs (this will still be a list even if there's only one exact match)
        """

        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = self.build_arg_string("expand", expand, "include_geopath", include_geopath, "date_utc", date.astimezone(timezone.utc).isoformat(), s=req)

        return [Run.load(**item) for item in self.call(req)["runs"]]

    def list_runs(self: Self,
                  route_id: int,
                  route_type: RouteType | None = None,
                  expand: Literal["All", "VehicleDescriptor", "VehiclePosition", "None"] | Iterable[Literal["All", "VehicleDescriptor", "VehiclePosition", "None"]] | None = None,
                  date: datetime | str | None = None
                  ) -> list[Run]:
        """Returns a list of all runs for the specified route identifier and, if provided, the specified route type.

        :param route_id: The route identifier
        :param route_type: The transport type of the specified route
        :param expand: Optional data to include in the response (server default is ``EXPAND_NONE``)
        :param date: Return only data from the specified date. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :return: A list of runs
        """

        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = self.build_arg_string("expand", expand, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, s=req)

        return [Run.load(**item) for item in self.call(req)["runs"]]

    @overload
    def get_stop(self: Self,
                 stop_id: int,
                 route_type: RouteType,
                 stop_location: bool | None = None,
                 stop_amenities: bool | None = None,
                 stop_accessibility: bool | None = None,
                 stop_contact: bool | None = None,
                 stop_ticket: bool | None = None,
                 gtfs: Literal[False, None] = None,
                 stop_staffing: bool | None = None,
                 stop_disruptions: bool | None = None
                 ) -> Stop:
        ...

    @overload
    def get_stop(self: Self,
                 stop_id: str,
                 route_type: RouteType,
                 stop_location: bool | None = None,
                 stop_amenities: bool | None = None,
                 stop_accessibility: bool | None = None,
                 stop_contact: bool | None = None,
                 stop_ticket: bool | None = None,
                 *,
                 gtfs: Literal[True],
                 stop_staffing: bool | None = None,
                 stop_disruptions: bool | None = None
                 ) -> Stop:
        ...

    @overload
    def get_stop(self: Self,
                 stop_id: str,
                 route_type: RouteType,
                 stop_location: bool | None,
                 stop_amenities: bool | None,
                 stop_accessibility: bool | None,
                 stop_contact: bool | None,
                 stop_ticket: bool | None,
                 gtfs: Literal[True],
                 stop_staffing: bool | None = None,
                 stop_disruptions: bool | None = None
                 ) -> Stop:
        ...

    def get_stop(self: Self,
                 stop_id: int | str,
                 route_type: RouteType,
                 stop_location: bool | None = None,
                 stop_amenities: bool | None = None,
                 stop_accessibility: bool | None = None,
                 stop_contact: bool | None = None,
                 stop_ticket: bool | None = None,
                 gtfs: bool | None = None,
                 stop_staffing: bool | None = None,
                 stop_disruptions: bool | None = None
                 ) -> Stop:
        """
        Returns the stop with the specified stop identifier and route type.

        :param stop_id: The stop identifier; must be ``str`` if ``gtfs`` is set to ``True``; otherwise, must be ``int``
        :param route_type: The transport type of the specified stop
        :param stop_location: Whether to include stop location information in the result (server default is ``False``)
        :param stop_amenities: Whether to include stop amenities information in the result (server default is ``False``)
        :param stop_accessibility: Whether to include stop accessibility information in the result (server default is ``False``)
        :param stop_contact: Whether to include operator contact details in the result (server default is ``False``)
        :param stop_ticket: Whether to include ticketing information in the result (server default is ``False``)
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is ``False``)
        :param stop_staffing: Whether to include stop staffing information in the result (server default is ``False``)
        :param stop_disruptions: Whether to include information about disruptions affecting the stop in the result (server default is ``False``)
        :return: Details of the specified stop
        """

        req = f"/v3/stops/{stop_id}/route_type/{route_type}"
        req = self.build_arg_string("stop_location", stop_location, "stop_amenities", stop_amenities, "stop_accessibility", stop_accessibility, "stop_contact", stop_contact, "stop_ticket", stop_ticket, "gtfs", gtfs, "stop_staffing", stop_staffing, "stop_disruptions", stop_disruptions, s=req)

        res = self.call(req)["stop"]
        return Stop.load(**res)

    def list_stops(self: Self,
                   route_id: int,
                   route_type: RouteType,
                   direction_id: int | None = None,
                   stop_disruptions: bool | None = None
                   ) -> list[Stop]:
        """
        Returns a list of all stops on the specified route.

        :param route_id: The route identifier
        :param route_type: The route type of the specified route
        :param direction_id: Specify a direction identifier to include stop sequence information in the list
        :param stop_disruptions: Whether to include stop disruption information
        :return: A list of all stops on the route
        """

        req = f"/v3/stops/route/{route_id}/route_type/{route_type}"
        req = self.build_arg_string("direction_id", direction_id, "stop_disruptions", stop_disruptions, s=req)
        return [Stop.load(**item) for item in self.call(req)["stops"]]

    def list_stops_near_location(self: Self,
                                 latitude: float,
                                 longitude: float,
                                 route_types: Iterable[RouteType] | None = None,
                                 max_results: int | None = None,
                                 max_distance: float | None = None,
                                 stop_disruptions: bool | None = None
                                 ) -> list[Stop]:
        """
        Returns a list of stops near the specified location.

        :param latitude: Latitude coordinate of the search location
        :param longitude: Longitude coordinate of the search location
        :param route_types: If specified, only return stops for the specified travel mode(s)
        :param max_results: Maximum number of stops to be returned (server default is 30)
        :param max_distance: Maximum radius from the specified location to search, in metres (server default is 300 metres)
        :param stop_disruptions: Whether to include stop disruption information (server default is ``False``)
        :return: A list of stops in the specified search parameters
        """

        req = f"/v3/stops/location/{latitude},{longitude}"
        req = self.build_arg_string("route_types", route_types, "max_results", max_results, "max_distance", max_distance, "stop_disruptions", stop_disruptions, s=req)

        return [Stop.load(**item) for item in self.call(req)["stops"]]

    # route_id is specified - force platform_numbers to be None
    # gtfs is not specified
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int,
                        route_id: int,
                        platform_numbers: None = None,
                        direction_id: int | None = None,
                        gtfs: Literal[False, None] = None,
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    # platform_numbers is specified - force route_id to be None
    # also for when both parameters are None
    # gtfs is not specified
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int,
                        route_id: None = None,
                        platform_numbers: Iterable[str | int] | None = None,
                        direction_id: int | None = None,
                        gtfs: Literal[False, None] = None,
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    # route_id is specified; gtfs is specified by keyword
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: int,
                        platform_numbers: None = None,
                        direction_id: int | None = None,
                        *,
                        gtfs: Literal[True],
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    # platform_numbers is specified; gtfs is specified by keyword
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: None = None,
                        platform_numbers: Iterable[str | int] | None = None,
                        direction_id: int | None = None,
                        *,
                        gtfs: Literal[True],
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    # route_id and gtfs are both specified by position
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: int,
                        platform_numbers: None,
                        direction_id: int | None,
                        gtfs: Literal[True],
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    # platform_numbers and gtfs are both specified by position
    # also for case where both route_id and platform_numbers are not specified
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: None,
                        platform_numbers: Iterable[str | int] | None,
                        direction_id: int | None,
                        gtfs: Literal[True],
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        ...

    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int | str,
                        route_id: int | None = None,
                        platform_numbers: Iterable[str | int] | None = None,
                        direction_id: int | None = None,
                        gtfs: bool | None = None,
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType | None = None,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        """
        Returns a list of departures from the specified stop.

        :param route_type: Transport mode identifier
        :param stop_id: Stop identifier
        :param route_id: If specified, show only departures for the specified route. Only one of 'route_id' and 'platform_numbers' should be specified.
        :param platform_numbers: If specified, show only departures from the specified platform numbers. Only one of 'route_id' and 'platform_numbers' should be specified.
        :param direction_id: If specified, show only departures travelling towards the specified direction
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is ``False``)
        :param include_advertised_interchange: Whether to include stop interchange information in result (server default is ``False``)
        :param date: If specified, show departures from the specified date and time (server default is current time). If 'look_backwards' is True, show departures that arrive at their terminating destinations prior to the specified date and time instead. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :param max_results: Return only this number of departures
        :param include_cancelled: Whether to include departures that are cancelled (server default is ``False``)
        :param look_backwards: If set to True, departures that arrive at their terminating destinations prior to the date and time specified in 'date' are returned instead (server default is ``False``)
        :param expand: Optional data to include in the response (server default is ``EXPAND_NONE``)
        :param include_geopath: Include the run's path geometry (server default is ``False``)
        :return: The requested departure information and any associated stop, route, run, direction and disruption data
        """

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = f"/v3/departures/route_type/{route_type}/stop/{stop_id}" + (f"/route/{route_id}" if route_id is not None else "")
        req = self.build_arg_string("platform_numbers", platform_numbers, "direction_id", direction_id, "gtfs", gtfs, "include_advertised_interchange", include_advertised_interchange, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "max_results", max_results, "include_cancelled", include_cancelled, "look_backwards", look_backwards, "expand", expand, "include_geopath", include_geopath, s=req)

        res = self.call(req)
        return DeparturesResponse.load(**res)

    @overload
    def list_disruptions(self: Self,
                         *,
                         route_types: Iterable[RouteType] | RouteType | None = None,
                         disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | None = None,
                         disruption_status: Literal["Current", "Planned"] | None = None
                         ):
        ...

    @overload
    def list_disruptions(self: Self,
                         route_id: int | None = None,
                         stop_id: int | None = None,
                         *,
                         disruption_status: Literal["Current", "Planned"] | None = None
                         ):
        ...

    def list_disruptions(self: Self,
                         route_id: int | None = None,
                         stop_id: int | None = None,
                         route_types: Iterable[RouteType] | RouteType | None = None,
                         disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | None = None,
                         disruption_status: Literal["Current", "Planned"] | None = None
                         ) -> list[Disruption]:
        """
        Returns a list of all disruptions or, if specified, the disruptions for the specified route and/or stop.

        :param route_id: If route identifier is specified, list only disruptions for the specified route. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param stop_id: If stop identifier is specified, list only disruptions for the specified stop. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param route_types: If specified, list only disruptions for the specified travel modes
        :param disruption_modes: If specified, list only disruptions for the specified disruption modes
        :param disruption_status: If specified, list only disruptions with the specified status
        :return: A list of disruptions
        """

        req = "/v3/disruptions" + (f"/route/{route_id}" if route_id is not None else "") + (f"/stop/{stop_id}" if stop_id is not None else "")
        req = self.build_arg_string("route_types", route_types, "disruption_modes", disruption_modes, "disruption_status", disruption_status, s=req)

        res = self.call(req)["disruptions"]
        ret = []
        for category in res.values():
            ret.extend(category)

        return [Disruption.load(**item) for item in ret]

    def get_disruption(self: Self, disruption_id: int) -> Disruption:
        """
        Retrieves the details of the disruption with the specified disruption identifier

        :param disruption_id: Disruption identifier
        :return: The disruption with the specified identifier
        """

        res = self.call(f"/v3/disruptions/{disruption_id}")["disruption"]
        return Disruption.load(**res)

    def list_disruption_modes(self: Self) -> list[dict[str, str | int]]:
        """
        Returns the names and identifiers of all disruption modes.

        :return: A list of disruption modes
        """

        return self.call("/v3/disruptions/modes")["disruption_modes"]

    def fare_estimate(self: Self,
                      zone_a: int,
                      zone_b: int,
                      touch_on: datetime | str | None = None,
                      touch_off: datetime | str | None = None,
                      is_free_fare_zone: bool | None = None,
                      route_types: Iterable[RouteType] | RouteType | None = None
                      ):
        """
        Returns the estimated fare for the specified journey details.

        :param zone_a: With zone_b, the lowest and highest zones travelled through (order independent)
        :param zone_b: As per zone_a
        :param touch_on: If specified, estimate the fare for the journey commencing at the specified touch on time. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :param touch_off: If specified, estimate the fare for the journey concluding at the specified touch off time. Defaults to ``ZoneInfo("Australia/Melbourne")`` if time zone not specified
        :param is_free_fare_zone: Whether the journey is entirely within a free fare zone
        :param route_types: If specified, estimate the fare for the journey travelling through the specified fare zone(s)
        :return: Object containing the estimated fares
        """

        if type(touch_on) is str:
            touch_on = datetime.fromisoformat(touch_on)
        if touch_on is not None and touch_on.tzinfo is None:
            touch_on = touch_on.replace(tzinfo=TZ_MELBOURNE)
        if type(touch_off) is str:
            touch_off = datetime.fromisoformat(touch_off)
        if touch_off is not None and touch_off.tzinfo is None:
            touch_off = touch_off.replace(tzinfo=TZ_MELBOURNE)

        req = f"/v3/fare_estimate/min_zone/{min(zone_a, zone_b)}/max_zone/{max(zone_a, zone_b)}"
        req = self.build_arg_string("touch_on", touch_on.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_on is not None else None, "touch_off", touch_off.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_off is not None else None, "is_free_fare_zone", is_free_fare_zone, "travelled_route_types", route_types, s=req)

        res = self.call(req)["FareEstimateResult"]
        return FareEstimate.load(**res)

    @overload
    def list_outlets(self: Self,
                     *,
                     max_results: int | None = None
                     ) -> list[Outlet]:
        ...

    @overload
    def list_outlets(self: Self,
                     latitude: float,
                     longitude: float,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ) -> list[Outlet]:
        ...

    def list_outlets(self: Self,
                     latitude: float | None = None,
                     longitude: float | None = None,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ) -> list[Outlet]:
        """
        Returns a list of all myki ticket outlets or, if specified, near the specified location.

        :param latitude: If specified together with ``longitude``, return ticket outlets near the specified location only
        :param longitude: If specified together with ``latitude``, return ticket outlets near the specified location only
        :param max_distance: Maximum radius from the specified location to search, in metres (server default is 300 metres)
        :param max_results: Maximum number of outlets to be returned (server default is 30)
        :return: A list of ticket outlets
        """

        req = "/v3/outlets" + (f"/location/{latitude},{longitude}" if latitude is not None and longitude is not None else "")
        req = self.build_arg_string("max_distance", max_distance, "max_results", max_results, s=req)

        res = self.call(req)["outlets"]
        return [Outlet.load(**item) for item in res]

    @overload
    def search(self: Self,
               search_term: str,
               route_types: Iterable[RouteType] | RouteType | None = None,
               *,
               include_outlets: bool | None = None,
               match_stop_by_suburb: bool | None = None,
               match_route_by_suburb: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ):
        ...

    @overload
    def search(self: Self,
               search_term: str,
               *,
               latitude: float,
               longitude: float,
               max_distance: float | None = None,
               include_outlets: bool | None = None,
               match_stop_by_suburb: bool | None = None,
               match_route_by_suburb: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ):
        ...

    @overload
    def search(self: Self,
               search_term: str,
               route_types: Iterable[RouteType] | RouteType | None,
               latitude: float,
               longitude: float,
               max_distance: float | None = None,
               include_outlets: bool | None = None,
               match_stop_by_suburb: bool | None = None,
               match_route_by_suburb: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ):
        ...

    def search(self: Self,
               search_term: str,
               route_types: Iterable[RouteType] | RouteType | None = None,
               latitude: float | None = None,
               longitude: float | None = None,
               max_distance: float | None = None,
               include_outlets: bool | None = None,
               match_stop_by_locality: bool | None = None,
               match_route_by_locality: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ) -> SearchResult:
        """
        Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

        If the search term is numeric or has fewer than 3 characters, the API will only return routes.

        :param search_term: Term to search
        :param route_types: Return stops and routes with the specified travel mode type(s) only
        :param latitude: Latitude coordinate of the location to search
        :param longitude: Longitude coordinate of the location to search
        :param max_distance: Radius, from centre location (specified in latitude and longitude parameters), of area to search in, in metres (server default is 300 metres)
        :param include_outlets: Whether to include ticket outlets in search result (server default is True)
        :param match_stop_by_locality: Whether to include stops in the search result where their localities match the search term (server default is ``True``)
        :param match_route_by_locality: Whether to include routes in the search result where their localities match the search term (server default is ``True``)
        :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is ``False``)
        :return: All matching stops, routes and ticket outlets
        """

        req = f"/v3/search/{urllib.parse.quote(search_term, safe="", encoding="utf-8")}"
        req = self.build_arg_string("route_types", route_types, "latitude", latitude, "longitude", longitude, "max_distance", max_distance, "include_outlets", include_outlets, "match_stop_by_suburb", match_stop_by_locality, "match_route_by_suburb", match_route_by_locality, "match_stop_by_gtfs_stop_id", match_stop_by_gtfs_stop_id, s=req)

        res = self.call(req)
        return SearchResult.load(**res)
