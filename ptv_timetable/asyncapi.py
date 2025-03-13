from aiohttp.client import ClientSession
from aiolimiter.leakybucket import AsyncLimiter
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from hashlib import sha1
from hmac import HMAC
from typing import Final, Literal, overload, Required, Self, TypedDict
import logging
import urllib.parse

from .types import *

__all__ = ["AsyncTimetableAPI", "METROPOLITAN_TRAIN", "METRO_TRAIN", "MET_TRAIN", "METRO", "TRAM", "BUS", "REGIONAL_TRAIN", "REG_TRAIN", "COACH", "VLINE", "EXPAND_ALL", "EXPAND_STOP", "EXPAND_ROUTE", "EXPAND_RUN", "EXPAND_DIRECTION", "EXPAND_DISRUPTION", "EXPAND_VEHICLE_DESCRIPTOR", "EXPAND_VEHICLE_POSITION", "EXPAND_NONE"]

type _Values = str | int | float | bool | datetime | _Record
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

class _PTVResponseType(TypedDict, total=False):
    directions: list[_Record]
    disruption: _Record
    disruptions: _Record
    disruption_modes: list[_Record]
    outlets: list[_Record]
    route: _Record
    routes: list[_Record]
    route_types: list[_Record]
    runs: list[_Record]
    stop: _Record
    stops: list[_Record]
    status: Required[TypedDict("Status", {"version": str, "health": int})]

class _FareEstimateResponseType(TypedDict, total=False):
    FareEstimateResult: _Record
    FareEstimateResultStatus: Required[TypedDict("FareEstimateResultStatus", {"Message": str, "StatusCode": int})]


type ExpandType = Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]
type RouteType = Literal[0, 1, 2, 3]

_logger: Final = logging.getLogger("ptv-timetable.ptv_timetable.asyncapi")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


class AsyncTimetableAPI(object):
    """Interface class for the PTV Timetable API."""

    def __init__(self: Self, dev_id: str | int, key: str, session: ClientSession, *, calls: int = 1, period: float = 10) -> None:
        """Creates a new :class:`AsyncTimetableAPI` instance with the supplied credentials.

        :param dev_id:  User ID
        :param key:     API request signing key (a UUID)
        :param session: Calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` instance to be used as a context manager. If you wish to let the instance handle the session, use the alternative constructor method :meth:`create` instead
        :param calls:   Maximum number of calls that can be made to the API within the specified ``period``
        :param period:  Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :return:        ``None``
        """

        if type(dev_id) not in (str, int):
            raise TypeError(f"devID must be str or int, not {type(dev_id).__name__}")
        if type(key) is not str:
            raise TypeError(f"key must be str, not {type(key).__name__}")

        if UUID_PATTERN.fullmatch(key) is None:
            raise ValueError(f"key is not a UUID string: {key}")

        if not isinstance(session, ClientSession):
            raise TypeError(f"session must be aiohttp.client.ClientSession, not {type(session).__name__}")

        self._dev_id: Final[str] = str(dev_id)
        """API user ID"""
        self._key: Final[bytes] = key.encode(encoding="ascii")
        """API request signing key"""

        self._limiter: Final[AsyncLimiter] = AsyncLimiter(calls, period)
        """HTTP requests rate limiter"""
        self._session: Final[ClientSession] = session
        """Asynchronous HTTP session"""
        self._is_user_session: bool = True
        """Whether the session is user-supplied (and therefore whether to auto-close on instance deletion)"""

        _logger.info("AsyncTimetableAPI instance created")
        return

    @classmethod
    async def create(cls: Callable[..., Self], dev_id: str | int, key: str, session: ClientSession | None = None, *, calls: int = 1, period: float = 10) -> Self:
        """Creates a new :class:`AsyncTimetableAPI` instance with the supplied credentials.

        :param dev_id:  User ID
        :param key:     API request signing key (a UUID)
        :param session: If specified, calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` instance to be used as a context manager (default is to create a new :class:`~aiohttp.ClientSession` instance to be used internally)
        :type session:  ~aiohttp.ClientSession | None
        :param calls:   Maximum number of calls that can be made to the API within the specified ``period``
        :param period:  Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :return:        The new instance
        """

        if session is None:
            instance = cls(dev_id=dev_id, key=key, session=ClientSession(), calls=calls, period=period)
            instance._is_user_session = False
        else:
            instance = cls(dev_id=dev_id, key=key, session=session, calls=calls, period=period)

        return instance

    def __del__(self: Self) -> None:
        """Closes the underlying HTTP session if it wasn't supplied by the user and logs the prospective deletion of the instance into the module logger once there are no more references to it in the program.

        Note that Python does not guarantee that this will be called for any instance.

        :return: ``None``
        """

        if not self._is_user_session:
            self._session.close()
        _logger.info("AsyncTimetableAPI instance deleted")
        return

    @staticmethod
    async def build_arg_string(*params: tuple[str, str | int | bool | Iterable[str | int] | None] | str | int | bool | Iterable[str | int] | None, s: str = "") -> str:
        """Builds a URL argument string using the specified parameter-value pairs. Automatically expands values that are :class:`~collections.abc.Iterable`. Ignores values that are ``None``.

        :param params: Tuples of (param, value) pairs, or the param and values themselves (must contain the exact number of arguments to complete the URL)
        :param s:      Optionally, the string to append to
        :return:       Modified URL string
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

    async def call(self: Self, request: str) -> _PTVResponseType | _FareEstimateResponseType:
        """Make the request to the API and format the result. This will be rate-limited based on the options provided when this instance was created.

        :param request: API request string
        :return:        Result of API request as a :class:`dict`
        :rtype:         dict[str, ...]
        """

        url = await self._encode_url(request)
        _logger.debug("Entering rate limit context manager")
        async with self._limiter:  # Rate limit requests
            _logger.debug("Requesting from: " + url)
            r = await self._session.request("get", url)
        try:
            r.raise_for_status()
        except Exception:
            _logger.error("", exc_info=True)
            raise
        _logger.debug("Awaiting JSON")
        result = await r.json()
        _logger.debug("Response: " + str(result))
        return result

    async def _encode_url(self: Self, request: str) -> str:
        """Appends the signature and base URL to the request string.

        :param request: API request string
        :return:        API request URL
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self._dev_id}"
        signature = HMAC(key=self._key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

    async def list_route_directions(self: Self, route_id: int) -> list[Direction]:
        """Returns the directions of travel for a particular route.

        :param route_id: The route identifier
        :return:         List of directions
        """

        return [await Direction.aload(**item) for item in (await self.call(f"/v3/directions/route/{route_id}"))["directions"]]

    async def get_direction(self: Self, direction_id: int, route_type: RouteType | None = None) -> list[Direction]:
        """Returns the direction(s) of travel in the database with the specified identifier and route type. If ``route_type`` isn't specified, this will return directions of travel for all modes (which are likely unrelated to one another). Note that this returns a :class:`list` in both cases.

        If the direction is shared by multiple routes (e.g. Flinders Street), a :class:`~ptv_timetable.types.Direction` object will be added to the :class:`list` for *each* route.

        :param direction_id: The direction identifier
        :param route_type:   Return the directions with the specified route type
        :type route_type:    ~typing.Literal[0, 1, 2, 3] | None
        :return:             List of directions
        """

        req = f"/v3/directions/{direction_id}" + (f"/route_type/{route_type}" if route_type is not None else "")
        return [await Direction.aload(**item) for item in (await self.call(req))["directions"]]

    async def get_pattern(self: Self,
                          run_ref: str | int,
                          route_type: RouteType,
                          stop_id: int | None = None,
                          date: datetime | str | None = None,
                          include_skipped_stops: bool | None = None,
                          expand: ExpandType | Iterable[ExpandType] | None = None,
                          include_geopath: bool | None = None
                          ) -> StoppingPattern:
        """Returns the stopping pattern of the specified run of the specified route type.

        :param run_ref:               The run identifier
        :param route_type:            The run's travel mode identifier
        :type route_type:             ~typing.Literal[0, 1, 2, 3]
        :param stop_id:               Include only the stop with the specified stop ID
        :param date:                  Doesn't appear to have any effect on the response
        :param include_skipped_stops: Include a list of stops that are skipped by the pattern (server default is ``False``)
        :param expand:                Optional data to include in the response (server default is :const:`~ptv_timetable.types.EXPAND_DISRUPTION`)
        :type expand:                 ~collections.abc.Iterable[~typing.Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]] | ~typing.Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"] | None
        :param include_geopath:       Include the pattern's path geometry (server default is ``False``)
        :return:                      The stopping pattern of the specified run
        """

        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = await self.build_arg_string("stop_id", stop_id, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "include_skipped_stops", include_skipped_stops, "expand", expand, "include_geopath", include_geopath, s=req)

        res = await self.call(req)
        return await StoppingPattern.aload(**res)

    async def get_route(self: Self, route_id: int, include_geopath: bool | None = None, geopath_date: datetime | str | None = None) -> Route:
        """Returns the details of the route with the specified route identifier.

        :param route_id:        The route identifier
        :param include_geopath: Include the route's path geometry (server default is ``False``)
        :param geopath_date:    Retrieve the path geometry valid at the specified geopath_date (ISO 8601 formatted if :class:`str`). Defaults to current server time. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :return:                Details of the specified route
        """

        if isinstance(geopath_date, str):
            geopath_date = datetime.fromisoformat(geopath_date)
        if geopath_date is not None and geopath_date.tzinfo is None:
            geopath_date = geopath_date.replace(tzinfo=TZ_MELBOURNE)

        req = await self.build_arg_string("include_geopath", include_geopath, "geopath_utc", geopath_date, s=f"/v3/routes/{route_id}")
        return await Route.aload(**(await self.call(req))["route"])

    async def list_routes(self: Self, route_types: Iterable[RouteType] | RouteType | None = None, route_name: str | None = None) -> list[Route]:
        """Returns all routes of all (or specified) types.

        :param route_types: Return only the routes of the specified type(s)
        :type route_types:  ~collections.abc.Iterable[~typing.Literal[0, 1, 2, 3]] | ~typing.Literal[0, 1, 2, 3] | None
        :param route_name:  Return the routes with names containing the specified substring
        :return:            A list of routes
        """

        req = await self.build_arg_string("route_types", route_types, "route_name", route_name, s="/v3/routes")
        return [await Route.aload(**item) for item in (await self.call(req))["routes"]]

    async def list_route_types(self: Self) -> list[TypedDict("RouteType", {"route_type_name": str, "route_type": int})]:
        """Returns the names and identifiers of all route types.

        :return: A list of records containing the aforementioned fields
        :rtype:  list[dict[~typing.Literal["route_type_name", "route_type"], str | int]]
        """

        return (await self.call("/v3/route_types"))["route_types"]

    async def get_run(self: Self,
                      run_ref: str | int,
                      route_type: RouteType | None = None,
                      expand: Iterable[Literal["All", "VehicleDescriptor", "VehiclePosition", "None"]] | Literal["All", "VehicleDescriptor", "VehiclePosition", "None"] | None = None,
                      date: datetime | str | None = None,
                      include_geopath: bool | None = None
                      ) -> list[Run]:
        """Returns a list of all runs with the specified run identifier and, optionally, the specified route type.

        :param run_ref:         The run identifier
        :param route_type:      Return runs of the specified type only
        :type route_type:       ~typing.Literal[0, 1, 2, 3] | None
        :param expand:          Optional data to include in the response (server default is :const:`~ptv_timetable.types.EXPAND_NONE`)
        :param date:            Return only data from the specified date. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :param include_geopath: Include the run's path geometry (server default is ``False``)
        :return:                A list of runs (this will still be a list even if there's only one exact match)
        """

        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = await self.build_arg_string("expand", expand, "include_geopath", include_geopath, "date_utc", date.astimezone(timezone.utc).isoformat(), s=req)

        return [await Run.aload(**item) for item in (await self.call(req))["runs"]]

    async def list_runs(self: Self,
                        route_id: int,
                        route_type: RouteType | None = None,
                        expand: Iterable[Literal["All", "VehicleDescriptor", "VehiclePosition", "None"]] | Literal["All", "VehicleDescriptor", "VehiclePosition", "None"] | None = None,
                        date: datetime | str | None = None
                        ) -> list[Run]:
        """Returns a list of all runs for the specified route identifier and, if provided, the specified route type.

        :param route_id:   The route identifier
        :param route_type: The transport type of the specified route
        :type route_type:  ~typing.Literal[0, 1, 2, 3] | None
        :param expand:     Optional data to include in the response (server default is :const:`~ptv_timetable.types.EXPAND_NONE`)
        :param date:       Return only data from the specified date. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :return:           A list of runs
        """

        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = await self.build_arg_string("expand", expand, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, s=req)

        return [await Run.aload(**item) for item in (await self.call(req))["runs"]]

    @overload
    async def get_stop(self: Self,
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
    async def get_stop(self: Self,
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
    async def get_stop(self: Self,
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

    async def get_stop(self: Self,
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
        """Returns the stop with the specified stop identifier and route type.

        :param stop_id:            The stop identifier; must be :class:`str` if ``gtfs`` is set to ``True``; otherwise, must be :class:`int`
        :param route_type:         The transport type of the specified stop
        :param stop_location:      Whether to include stop location information in the result (server default is ``False``)
        :param stop_amenities:     Whether to include stop amenities information in the result (server default is ``False``)
        :param stop_accessibility: Whether to include stop accessibility information in the result (server default is ``False``)
        :param stop_contact:       Whether to include operator contact details in the result (server default is ``False``)
        :param stop_ticket:        Whether to include ticketing information in the result (server default is ``False``)
        :param gtfs:               Whether the value specified in ``stop_id`` is a General Transit Feed Specification identifier (server default is ``False``)
        :param stop_staffing:      Whether to include stop staffing information in the result (server default is ``False``)
        :param stop_disruptions:   Whether to include information about disruptions affecting the stop in the result (server default is ``False``)
        :return:                   Details of the specified stop
        """

        req = f"/v3/stops/{stop_id}/route_type/{route_type}"
        req = await self.build_arg_string("stop_location", stop_location, "stop_amenities", stop_amenities, "stop_accessibility", stop_accessibility, "stop_contact", stop_contact, "stop_ticket", stop_ticket, "gtfs", gtfs, "stop_staffing", stop_staffing, "stop_disruptions", stop_disruptions, s=req)

        res = (await self.call(req))["stop"]
        return await Stop.aload(**res)

    async def list_stops(self: Self,
                         route_id: int,
                         route_type: RouteType,
                         direction_id: int | None = None,
                         stop_disruptions: bool | None = None
                         ) -> list[Stop]:
        """Returns a list of all stops on the specified route.

        :param route_id:         The route identifier
        :param route_type:       The route type of the specified route
        :type route_type:        ~typing.Literal[0, 1, 2, 3]
        :param direction_id:     Specify a direction identifier to include stop sequence information in the list
        :param stop_disruptions: Whether to include stop disruption information
        :return:                 A list of all stops on the route
        """

        req = f"/v3/stops/route/{route_id}/route_type/{route_type}"
        req = await self.build_arg_string("direction_id", direction_id, "stop_disruptions", stop_disruptions, s=req)
        res = (await self.call(req))["stops"]
        return [await Stop.aload(**item) for item in res]

    async def list_stops_near_location(self: Self,
                                       latitude: float,
                                       longitude: float,
                                       route_types: Iterable[RouteType] | RouteType | None = None,
                                       max_results: int | None = None,
                                       max_distance: float | None = None,
                                       stop_disruptions: bool | None = None
                                       ) -> list[Stop]:
        """Returns a list of stops near the specified location.

        :param latitude:         Latitude coordinate of the search location
        :param longitude:        Longitude coordinate of the search location
        :param route_types:      If specified, only return stops for the specified travel mode(s)
        :type route_types:       collections.abc.Iterable[typing.Literal[0, 1, 2, 3]] | typing.Literal[0, 1, 2, 3] | None
        :param max_results:      Maximum number of stops to be returned (server default is 30)
        :param max_distance:     Maximum radius from the specified location to search, in metres (server default is 300 metres)
        :param stop_disruptions: Whether to include stop disruption information (server default is ``False``)
        :return:                 A list of stops in the specified search parameters
        """

        req = f"/v3/stops/location/{latitude},{longitude}"
        req = await self.build_arg_string("route_types", route_types, "max_results", max_results, "max_distance", max_distance, "stop_disruptions", stop_disruptions, s=req)
        res = (await self.call(req))["stops"]
        return [await Stop.aload(**item) for item in res]

    # route_id is specified - force platform_numbers to be None
    # gtfs is not specified
    @overload
    async def list_departures(self: Self,
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
    async def list_departures(self: Self,
                              route_type: RouteType,
                              stop_id: int,
                              route_id: None = None,
                              platform_numbers: Iterable[str | int] | str | int | None = None,
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
    async def list_departures(self: Self,
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
    async def list_departures(self: Self,
                              route_type: RouteType,
                              stop_id: str,
                              route_id: None = None,
                              platform_numbers: Iterable[str | int] | str | int | None = None,
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
    async def list_departures(self: Self,
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
    async def list_departures(self: Self,
                              route_type: RouteType,
                              stop_id: str,
                              route_id: None,
                              platform_numbers: Iterable[str | int] | str | int | None,
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

    async def list_departures(self: Self,
                              route_type: RouteType,
                              stop_id: int | str,
                              route_id: int | None = None,
                              platform_numbers: Iterable[str | int] | str | int | None = None,
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
        """Returns a list of departures from the specified stop.

        :param route_type:                     Transport mode identifier
        :param stop_id:                        Stop identifier; must be :class:`str` if ``gtfs`` is set to ``True``; otherwise, must be :class:`int`
        :param route_id:                       If specified, show only departures for the specified route. Only one of '`route_id`' and '`platform_numbers`' should be specified.
        :param platform_numbers:               If specified, show only departures from the specified platform numbers. Only one of '`route_id`' and '`platform_numbers`' should be specified.
        :param direction_id:                   If specified, show only departures travelling towards the specified direction
        :param gtfs:                           Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is ``False``)
        :param include_advertised_interchange: Whether to include stop interchange information in result (server default is ``False``)
        :param date:                           If specified, show departures from the specified date (server default is current date). Appears to ignore the time fields. If 'look_backwards' is True, show departures that arrive at their terminating destinations prior to the specified date instead. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :param max_results:                    Return only this number of departures
        :param include_cancelled:              Whether to include departures that are cancelled (server default is ``False``)
        :param look_backwards:                 If set to ``True``, departures that arrive at their terminating destinations prior to the date specified in 'date' are returned instead (server default is ``False``)
        :param expand:                         Optional data to include in the response (server default is :const:`~ptv_timetable.types.EXPAND_NONE`)
        :param include_geopath:                Include the run's path geometry (server default is ``False``)
        :return:                               The requested departure information and any associated stop, route, run, direction and disruption data
        """

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=TZ_MELBOURNE)

        req = f"/v3/departures/route_type/{route_type}/stop/{stop_id}" + (f"/route/{route_id}" if route_id is not None else "")
        req = await self.build_arg_string("platform_numbers", platform_numbers, "direction_id", direction_id, "gtfs", gtfs, "include_advertised_interchange", include_advertised_interchange, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "max_results", max_results, "include_cancelled", include_cancelled, "look_backwards", look_backwards, "expand", expand, "include_geopath", include_geopath, s=req)

        res = await self.call(req)
        return await DeparturesResponse.aload(**res)

    @overload
    async def list_disruptions(self: Self,
                               *,
                               route_types: Iterable[RouteType] | RouteType | None = None,
                               disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100] | None = None,
                               disruption_status: Literal["Current", "Planned"] | None = None
                               ) -> list[Disruption]:
        ...

    @overload
    async def list_disruptions(self: Self,
                               route_id: int | None = None,
                               stop_id: int | None = None,
                               *,
                               disruption_status: Literal["Current", "Planned"] | None = None
                               ) -> list[Disruption]:
        ...

    async def list_disruptions(self: Self,
                               route_id: int | None = None,
                               stop_id: int | None = None,
                               route_types: Iterable[RouteType] | RouteType | None = None,
                               disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100] | None = None,
                               disruption_status: Literal["Current", "Planned"] | None = None
                               ) -> list[Disruption]:
        """Returns a list of all disruptions or, if specified, the disruptions for the specified route and/or stop.

        :param route_id:          If route identifier is specified, list only disruptions for the specified route. If both ``route_id`` and ``stop_id`` are specified, list only disruptions for the specified route and stop
        :param stop_id:           If stop identifier is specified, list only disruptions for the specified stop. If both ``route_id`` and ``stop_id`` are specified, list only disruptions for the specified route and stop
        :param route_types:       If specified, list only disruptions for the specified travel modes. Does not work with ``route_id`` or ``stop_id``
        :param disruption_modes:  If specified, list only disruptions for the specified disruption modes. Does not work with ``route_id`` or ``stop_id``
        :param disruption_status: If specified, list only disruptions with the specified status
        :return:                  A list of disruptions
        """

        req = "/v3/disruptions" + (f"/route/{route_id}" if route_id is not None else "") + (f"/stop/{stop_id}" if stop_id is not None else "")
        req = await self.build_arg_string("route_types", route_types, "disruption_modes", disruption_modes, "disruption_status", disruption_status, s=req)

        res = (await self.call(req))["disruptions"]
        ret = []
        for category in res.values():
            ret.extend(category)

        return [await Disruption.aload(**item) for item in ret]

    async def get_disruption(self: Self, disruption_id: int) -> Disruption:
        """Retrieves the details of the disruption with the specified disruption identifier

        :param disruption_id: Disruption identifier
        :return:              The disruption with the specified identifier
        """

        res = (await self.call(f"/v3/disruptions/{disruption_id}"))["disruption"]
        return await Disruption.aload(**res)

    async def list_disruption_modes(self: Self) -> list[TypedDict("DisruptionMode", {"disruption_mode": int, "disruption_mode_name": str})]:
        """Returns the names and identifiers of all disruption modes.

        :return: A list of disruption modes
        :rtype: list[dict[~typing.Literal["disruption_mode", "disruption_mode_name"], int | str]]
        """

        return (await self.call("/v3/disruptions/modes"))["disruption_modes"]

    async def fare_estimate(self: Self,
                            zone_a: int,
                            zone_b: int,
                            touch_on: datetime | str | None = None,
                            touch_off: datetime | str | None = None,
                            is_free_fare_zone: bool | None = None,
                            route_types: Iterable[RouteType] | RouteType | None = None
                            ) -> FareEstimate:
        """Returns the estimated fare for the specified journey details.

        :param zone_a:            With zone_b, the lowest and highest zones travelled through (order independent)
        :param zone_b:            As per zone_a
        :param touch_on:          If specified, estimate the fare for the journey commencing at the specified touch on time. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :param touch_off:         If specified, estimate the fare for the journey concluding at the specified touch off time. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
        :param is_free_fare_zone: Whether the journey is entirely within a free fare zone
        :param route_types:       If specified, estimate the fare for the journey travelling through the specified fare zone(s)
        :type route_types:        ~collections.abc.Iterable[~typing.Literal[0, 1, 2, 3]] | ~typing.Literal[0, 1, 2, 3] | None
        :return:                  Object containing the estimated fares
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
        req = await self.build_arg_string("touch_on", touch_on.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_on is not None else None, "touch_off", touch_off.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_off is not None else None, "is_free_fare_zone", is_free_fare_zone, "travelled_route_types", route_types, s=req)

        res = (await self.call(req))["FareEstimateResult"]
        return await FareEstimate.aload(**res)

    @overload
    async def list_outlets(self: Self,
                           *,
                           max_results: int | None = None
                           ) -> list[Outlet]:
        ...

    @overload
    async def list_outlets(self: Self,
                           latitude: float,
                           longitude: float,
                           max_distance: float | None = None,
                           max_results: int | None = None
                           ) -> list[Outlet]:
        ...

    async def list_outlets(self: Self,
                           latitude: float | None = None,
                           longitude: float | None = None,
                           max_distance: float | None = None,
                           max_results: int | None = None
                           ) -> list[Outlet]:
        """Returns a list of all myki ticket outlets or, if specified, near the specified location.

        :param latitude:     If specified together with ``longitude``, return ticket outlets near the specified location only
        :param longitude:    If specified together with ``latitude``, return ticket outlets near the specified location only
        :param max_distance: Maximum radius from the specified location to search, in metres (server default is 300 metres). Can only be used if ``latitude`` and ``longitude`` are specified
        :param max_results:  Maximum number of outlets to be returned (server default is 30)
        :return:             A list of ticket outlets
        """

        req = "/v3/outlets" + (f"/location/{latitude},{longitude}" if latitude is not None and longitude is not None else "")
        req = await self.build_arg_string("max_distance", max_distance, "max_results", max_results, s=req)

        res = (await self.call(req))["outlets"]
        return [await Outlet.aload(**item) for item in res]

    @overload
    async def search(self: Self,
                     search_term: str,
                     route_types: Iterable[RouteType] | RouteType | None = None,
                     *,
                     include_outlets: bool | None = None,
                     match_stop_by_suburb: bool | None = None,
                     match_route_by_suburb: bool | None = None,
                     match_stop_by_gtfs_stop_id: bool | None = None
                     ) -> SearchResult:
        ...

    @overload
    async def search(self: Self,
                     search_term: str,
                     *,
                     latitude: float,
                     longitude: float,
                     max_distance: float | None = None,
                     include_outlets: bool | None = None,
                     match_stop_by_suburb: bool | None = None,
                     match_route_by_suburb: bool | None = None,
                     match_stop_by_gtfs_stop_id: bool | None = None
                     ) -> SearchResult:
        ...

    @overload
    async def search(self: Self,
                     search_term: str,
                     route_types: Iterable[RouteType] | RouteType | None,
                     latitude: float,
                     longitude: float,
                     max_distance: float | None = None,
                     include_outlets: bool | None = None,
                     match_stop_by_suburb: bool | None = None,
                     match_route_by_suburb: bool | None = None,
                     match_stop_by_gtfs_stop_id: bool | None = None
                     ) -> SearchResult:
        ...

    async def search(self: Self,
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
        """Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

        If the search term is numeric or has fewer than 3 characters, the API will only return routes.

        :param search_term:                Term to search
        :param route_types:                Return stops and routes with the specified travel mode type(s) only
        :param latitude:                   Latitude coordinate of the location to search
        :param longitude:                  Longitude coordinate of the location to search
        :param max_distance:               Radius, from centre location (specified in latitude and longitude parameters), of area to search in, in metres (server default is 300 metres). Can only be used if ``latitude`` and ``longitude`` are specified
        :param include_outlets:            Whether to include ticket outlets in search result (server default is ``True``)
        :param match_stop_by_locality:     Whether to include stops in the search result where their localities match the search term (server default is ``True``)
        :param match_route_by_locality:    Whether to include routes in the search result where their localities match the search term (server default is ``True``)
        :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is ``False``)
        :return:                           All matching stops, routes and ticket outlets
        """

        req = f"/v3/search/{urllib.parse.quote(search_term, safe="", encoding="utf-8")}"
        req = await self.build_arg_string("route_types", route_types, "latitude", latitude, "longitude", longitude, "max_distance", max_distance, "include_outlets", include_outlets, "match_stop_by_suburb", match_stop_by_locality, "match_route_by_suburb", match_route_by_locality, "match_stop_by_gtfs_stop_id", match_stop_by_gtfs_stop_id, s=req)

        res = await self.call(req)
        return await SearchResult.aload(**res)
