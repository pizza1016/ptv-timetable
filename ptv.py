from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from defusedxml.ElementTree import XML
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from sys import stderr, stdout
from typing import Any, Final, Literal, overload, Self, TypeVar
from xml.etree.ElementTree import Element
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import tzdata

__all__ = ["APIClient", "MET_TRAIN", "METRO", "TRAM", "BUS", "REG_TRAIN", "COACH", "VLINE", "ALL", "STOP", "ROUTE", "RUN", "DIRECTION", "DISRUPTION", "VEHICLE_DESCRIPTOR", "VEHICLE_POSITION", "NONE"]

_T = TypeVar("_T")

type _Values = str | int | float | bool | datetime
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

type _Departure = dict[str, str | int | bool | datetime | list[int] | list[_SkippedStop]]
type _Direction = dict[str, str | int]
type _Disruption = dict[str, str | int | datetime | list[_Route] | list[_Stop]]
type _Geopath = list[dict[str, str | int | list[str]]]
type _Route = dict[str, str | int | dict[str, str] | _Geopath]
type _RouteType = dict[str, str | int]
type _Run = dict[str, str | int | _VehiclePosition | _VehicleDescriptor | _Geopath]
type _SkippedStop = dict[str, str | int]
type _Stop = dict[str, str | int | float | _TicketingInfo]
type _TicketingInfo = dict[str, str | bool | list[int]]
type _VehicleDescriptor = dict[str, str | bool] | None
type _VehiclePosition = dict[str, str | int | datetime] | None

type ExpandType = Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]
type RouteType = Literal[0, 1, 2, 3]

TZ_MELBOURNE = ZoneInfo("Australia/Melbourne")
UUID_PATTERN = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")

MET_TRAIN: Literal[0] = 0
"""Metropolitan trains"""
METRO: Literal[0] = 0
"""Metropolitan trains"""
TRAM: Literal[1] = 1
"""Metropolitan trams"""
BUS: Literal[2] = 2
"""Metropolitan & regional buses"""
REG_TRAIN: Literal[3] = 3
"""Regional trains & coaches"""
COACH: Literal[3] = 3
"""Regional trains & coaches"""
VLINE: Literal[3] = 3
"""Regional trains & coaches"""

ALL: Literal["All"] = "All"
"""Return all object properties in full"""
STOP: Literal["Stop"] = "Stop"
"""Return stop properties"""
ROUTE: Literal["Route"] = "Route"
"""Return route properties"""
RUN: Literal["Run"] = "Run"
"""Return run properties"""
DIRECTION: Literal["Direction"] = "Direction"
"""Return direction properties"""
DISRUPTION: Literal["Disruption"] = "Disruption"
"""Return disruption properties"""
VEHICLE_DESCRIPTOR: Literal["VehicleDescriptor"] = "VehicleDescriptor"
"""Return vehicle descriptor properties"""
VEHICLE_POSITION: Literal["VehiclePosition"] = "VehiclePosition"
"""Return vehicle position properties"""
NONE: Literal["None"] = "None"
"""Don't return any object properties"""

logger = logging.getLogger("ptv")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(stdout))


class APIDataClass:
    def __init__(self: Self, **kwargs: Any): ...


@dataclass(kw_only=True)
class Geopath(APIDataClass):
    direction_id: int
    valid_from: str
    valid_to: str
    paths: list[str]


@dataclass(kw_only=True)
class Departure(APIDataClass):
    """Represents a specific departure from a specific stop."""

    stop_id: int
    route_id: int
    direction_id: int
    run_ref: str
    disruption_ids: list[int]
    scheduled_departure: datetime
    estimated_departure: datetime | None
    at_platform: bool
    platform_number: str
    flags: str
    departure_sequence: int


@dataclass(kw_only=True)
class Stop(APIDataClass):
    stop_distance: float
    stop_suburb: str
    stop_name: str
    stop_id: int
    route_type: int
    stop_latitude: float
    stop_longitude: float
    stop_landmark: str
    stop_sequence: int


@dataclass(kw_only=True)
class Route(APIDataClass):
    route_type: int
    route_id: int
    route_name: str
    route_number: str
    route_gtfs_id: str
    geopath: list[Geopath]


@dataclass(kw_only=True)
class VehiclePosition(APIDataClass):
    latitude: float | None
    longitude: float | None
    easting: float | None
    northing: float | None
    direction: str
    bearing: float | None
    supplier: str
    as_of: datetime
    expires: datetime


@dataclass(kw_only=True)
class VehicleDescriptor(APIDataClass):
    operator: str
    id: str
    low_floor: bool | None
    air_conditioned: bool | None
    description: str
    supplier: str
    length: str


@dataclass(kw_only=True)
class Run(APIDataClass):
    run_ref: str
    route_id: int
    route_type: int
    final_stop_id: int
    destination_name: str
    status: str
    direction_id: int
    run_sequence: int
    express_stop_count: int
    vehicle_position: VehiclePosition | None
    vehicle_descriptor: VehicleDescriptor | None
    geopath: list[Geopath]
    interchange: dict


@dataclass(kw_only=True)
class Direction(APIDataClass):
    direction_id: int
    direction_name: str
    route_id: int
    route_type: int


@dataclass(kw_only=True)
class Disruption(APIDataClass):
    disruption_id: int
    title: str
    url: str
    description: str
    disruption_status: str
    disruption_type: str
    published_on: datetime
    last_updated: datetime
    from_date: datetime
    to_date: datetime
    routes: list[Route]
    stops: list[Stop]
    colour: str
    display_on_board: bool
    display_status: bool


@dataclass(kw_only=True)
class DeparturesResponse(APIDataClass):
    departures: list[Departure]
    stops: dict[int, Stop]
    routes: dict[int, Route]
    runs: dict[str, Run]
    directions: dict[int, Direction]
    disruptions: dict[int, Disruption]


class APIClient:
    """Interface class with the PTV Timetable API."""

    def __init__(self: Self, dev_id: str | int, key: str) -> None:
        """Initialises a PTVInterface instance with the supplied credentials.

        :param dev_id: User ID
        :param key: API request signing key (a UUID)
        :return: None
        """
        
        if not isinstance(dev_id, (str, int)):
            raise TypeError(f"devID must be type str or int ({type(dev_id)} provided)")
        elif not isinstance(key, str):
            raise TypeError(f"key must be type str ({type(key)} provided)")

        if UUID_PATTERN.fullmatch(key) is None:
            raise ValueError(f"Key is not a UUID string: {key}")

        self._devID: Final[str] = str(dev_id)
        self._key: Final[bytes] = key.encode(encoding="ascii")
        return

    @staticmethod
    def build_arg_string(*params: tuple[str, str | int | ExpandType | RouteType | Iterable[str | int | ExpandType | RouteType] | None] | str | int | ExpandType | RouteType | Iterable[str | int | ExpandType | RouteType] | None, s: str = "") -> str:
        """Builds a URL argument string using the specified parameter-value pairs. Automatically expands values that are Iterable. Ignores values that are None.

        :param params: Tuples of (param, value) pairs, or the param and values themselves (must contain the exact number of arguments to complete the URL)
        :param s: Optionally, the string to append to
        :return: Modified URL string
        """

        i = 0
        while i < len(params):
            if isinstance(params[i], tuple):
                if isinstance(params[i][1], str | int):
                    s += f"{"&" if "?" in s else "?"}{params[i][0]}={params[i][1]}"
                elif isinstance(params[i][1], bool):
                    s += f"{"&" if "?" in s else "?"}{params[i][0]}={"true" if params[i][1] else "false"}"
                elif isinstance(params[i][1], Iterable):
                    for value in params[i][1]:
                        s += f"{"&" if "?" in s else "?"}{params[i][0]}={value}"
                elif params[i][1] is not None:
                    raise TypeError(f"Argument {i} ({params[i]}) contains unsupported types")
                i += 1
            elif isinstance(params[i], str):
                if i + 1 >= len(params):
                    raise ValueError(f"Not enough arguments provided (missing value for {params[i]})")
                elif isinstance(params[i + 1], str | int):
                    s += f"{"&" if "?" in s else "?"}{params[i]}={params[i + 1]}"
                elif isinstance(params[i + 1], bool):
                    s += f"{"&" if "?" in s else "?"}{params[i]}={"true" if params[i + 1] else "false"}"
                elif isinstance(params[i + 1], Iterable):
                    for value in params[i + 1]:
                        s += f"{"&" if "?" in s else "?"}{params[i]}={value}"
                elif params[i + 1] is not None:
                    raise TypeError(f"Argument {i + 1} ({params[i + 1]}) is not str, int or Iterable[str | int]")
                i += 2
            else:
                raise TypeError(f"Argument {i} ({params[i]}) is not tuple or str")

        return s

    @sleep_and_retry
    @limits(calls=1, period=10)  # 1 call every 10 seconds
    def call(self: Self, request: str) -> dict[str, _Record | list[_Record]]:
        """Make the request to the API and format the result.

        :param request: API request string
        :return: Result of API request as a dict
        """

        url = self._encode_url(request)
        logger.debug(url)
        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        logger.debug(str(result))
        return result
    
    def _encode_url(self: Self, request: str) -> str:
        """Appends the signature and base URL to the request string.
        
        :param request: API request string
        :return: API request URL
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self._devID}"
        signature = HMAC(key=self._key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

    def _convert_fields(self: Self, obj: _T) -> _T:
        if type(obj) is dict:  # Only convert fields of dicts; everything else passes through unchanged
            single_record_t9n_table = {}
            multi_record_t9n_table = {"stops": Stop, "routes": Route, "directions": Direction, "disruptions": Disruption, "geopath": Geopath}
            time_fields = {"scheduled_departure_utc": "scheduled_departure", "estimated_departure_utc": "estimated_departure", "published_on": "published_on", "last_updated": "last_updated", "from_date": "from_date", "to_date": "to_date"}  # maps keys used by servers to keys used in this module's data structures
            time_fields_to_update = []

            for key in obj:
                # Convert children first - this is the recursive case; base case is when type is not dict or list (do nothing)
                if type(obj[key]) is list:
                    for i in range(len(obj[key])):
                        if type(obj[key][i]) is dict:
                            obj[key][i] = self._convert_fields(obj[key][i])  # Convert children fields regardless of type
                            if key in multi_record_t9n_table:  # Then if item type is a specified dataclass, convert the item
                                obj[key][i] = multi_record_t9n_table[key](**obj[key][i])
                    continue  # Don't convert the list itself
                elif type(obj[key]) is dict:
                    if key in multi_record_t9n_table:  # If the dict is a mapping of identifiers to objects
                        for item_key in obj[key]:
                            obj[key][item_key] = self._convert_fields(obj[key][item_key])  # Convert children fields
                            obj[key][item_key] = multi_record_t9n_table[key](obj[key][item_key])  # Then convert item itself
                    else:  # If the dict is a single object
                        obj[key] = self._convert_fields(obj[key])
                        if key in single_record_t9n_table:
                            obj[key] = single_record_t9n_table[key](obj[key])
                    continue
                elif key in time_fields.keys():  # update timestamps to datetime objects
                    time_fields_to_update.append(key)  # can't add or remove fields while dict is being iterated, so postpone update

            for key in time_fields_to_update:
                obj[time_fields[key]] = datetime.fromisoformat(obj[key]).astimezone(TZ_MELBOURNE) if obj[key] is not None else None
                del obj[key]

        return obj

    def list_route_directions(self: Self, route_id: int) -> list[_Direction]:
        """Returns the directions of travel for a particular route.

        Returned records contain these fields:
        "route_direction_description" (str): Description of the travel direction
        "direction_id" (int): Travel direction identifier
        "direction_name" (str): Label of the travel direction
        "route_id" (int): Route identifier
        "route_type" (int): Travel mode identifier

        :param route_id: The route ID number
        :return: A list of records containing the aforementioned fields
        """

        return self.call(f"/v3/directions/route/{route_id}")["directions"]

    def list_directions(self: Self, direction_id: int, route_type: RouteType | None = None) -> list[_Direction]:
        """Returns all directions of travel in the database for all (or the specified) route type(s).

        Returned records contain these fields:
        "route_direction_description" (str): Description of the travel direction
        "direction_id" (int): Travel direction identifier
        "direction_name" (str): Label of the travel direction
        "route_id" (int): Route identifier
        "route_type" (int): Travel mode identifier

        :param direction_id: The direction ID number
        :param route_type: Return only the directions with the specified route type
        :return: A list of records containing the aforementioned fields
        """

        return self.call(f"/v3/directions/{direction_id}{f"/route_type/{route_type}" if route_type is not None else ""}")["directions"]

    def get_pattern(self: Self,
                    run_ref: str,
                    route_type: RouteType,
                    stop_id: int | None = None,
                    date: datetime | str | None = None,
                    include_skipped_stops: bool = False,
                    expand: ExpandType | Iterable[ExpandType] = NONE,
                    include_geopath: bool = False
                    ) -> list[_Departure]:
        """Returns the stopping pattern of the specified run of the specified route type.

        Returned records contain these fields:
        "skipped_stops" (list[dict[str, int | str]]): A list of stops skipped by this stopping pattern after this stop
        "stop_id" (int): Stop identifier
        "route_id" (int): Route identifier
        "run_id" (int): Run identifier (deprecated)
        "run_ref" (str): Run identifier
        "direction_id" (int): Travel direction identifier
        "disruption_ids" (list[int]): List of identifiers of disruptions that are affecting the service
        "scheduled_departure_utc" (datetime): Scheduled time of departure from this stop per the timetable
        "estimated_departure_utc" (datetime): Estimated actual time of departure from this stop based on real-time location data
        "at_platform" (bool): Indicates whether the train is currently at the platform; always returns False for all other modes
        "platform_number" (str): Identifier of the platform where the train will depart/has departed from
        "flags" (str): Flag indicating special condition for run (e.g. RR Reservations Required, GC Guaranteed Connection, DOO Drop Off Only, PUO Pick Up Only, MO Mondays only, TU Tuesdays only, WE Wednesdays only, TH Thursdays only, FR Fridays only, SS School days only; ignore E flag)
        "departure_sequence" (int): Sort key for the order of departures for this service

        :param run_ref: The run identifier
        :param route_type: The run's travel mode identifier
        :param stop_id: Include only the stop with the specified stop ID
        :param date: TODO
        :param include_skipped_stops: Include a list of stops that are skipped by the pattern
        :param expand: TODO
        :param include_geopath: Include the pattern's geopath data
        :return: A list of records containing the aforementioned fields
        """

        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("stop_id", stop_id, "date_utc", date.astimezone(timezone.utc).isoformat(), "include_skipped_stops", "true" if include_skipped_stops else None, "expand", expand, "include_geopath", "true" if include_geopath else None, s=req)

        res = self.call(req)["departures"]
        for record in res:
            record["scheduled_departure_utc"] = datetime.fromisoformat(record["scheduled_departure_utc"]).astimezone(TZ_MELBOURNE) if record["scheduled_departure_utc"] is not None else None
            record["estimated_departure_utc"] = datetime.fromisoformat(record["estimated_departure_utc"]).astimezone(TZ_MELBOURNE) if record["estimated_departure_utc"] is not None else None
        return res

    def get_route(self: Self, route_id: int, include_geopath: bool = False, geopath_utc: str | None = None) -> _Route:
        """Returns the details of the route with the specified route ID.

        Returned record contains these fields:
        "route_service_status" (dict[str, str]): Status of services on the route
        "route_type" (int): Travel mode identifier
        "route_id" (int): Route identifier
        "route_name" (str): Route name
        "route_number" (str): Route number (publicly)
        "route_gtfs_id" (str): Route identifier in the General Transit Feed Specification
        "geopath" (list[dict[str, str | int | list[str]]]): The route's geometry as a sequence of coordinates

        :param route_id: The route ID number
        :param include_geopath: Include the route's geopath data
        :param geopath_utc: ISO 8601 UTC date to filter geopaths by
        :return: A record containing the aforementioned fields
        """

        req = self.build_arg_string("include_geopath", "true" if include_geopath else None, "geopath_utc", geopath_utc, s=f"/v3/routes/{route_id}")
        return self.call(req)["route"]

    def list_routes(self: Self, route_types: Iterable[RouteType] | None = None, route_name: str | None = None) -> list[_Route]:
        """Returns all routes of all (or specified) types.

        Returned records contain these fields:
        "route_service_status" (dict[str, str]): Status of services on the route
        "route_type" (int): Travel mode identifier
        "route_id" (int): Route identifier
        "route_name" (str): Route name
        "route_number" (str): Route number (publicly)
        "route_gtfs_id" (str): Route identifier in the General Transit Feed Specification
        "geopath" (list[dict[str, str | int | list[str]]]): The route's geometry as a sequence of coordinates

        :param route_types: Return only the routes of the specified type(s)
        :param route_name: Return the routes with names containing the specified substring
        :return: A list of records containing the aforementioned fields
        """

        return self.call(self.build_arg_string("route_types", route_types, "route_name", route_name, s="/v3/routes"))["routes"]

    def list_route_types(self: Self) -> list[_RouteType]:
        """Returns the names and identifiers of all route types.

        Returned records contain these fields:
        "route_type_name" (str):
        "route_type" (int):

        :return: A list of records containing the aforementioned fields
        """

        return self.call("/v3/route_types")["route_types"]

    def get_run(self: Self,
                run_ref: str,
                route_type: RouteType | None = None,
                expand: ExpandType = NONE,
                date: datetime | str | None = None,
                include_geopath: bool | None = None
                ) -> list[_Run]:
        """Returns a list of all runs for the specified run identifier and, optionally, the specified route type.

        Returned records contain these fields:
        "run_id" (int): Run identifier (deprecated)
        "run_ref" (str): Run identifier
        "route_id" (int): Route identifier
        "route_type" (int): Travel mode identifier
        "final_stop_id" (int): Identifier of final stop on run
        "destination_name" (str): Destination label
        "status" (str): Current status of run (i.e. whether the service is on time, delayed, etc.); "scheduled" if status unavailable
        "direction_id" (int): Travel direction identifier
        "run_sequence" (int): Sort key for chronological order in a list of runs having the same route and direction of travel
        "express_stop_count" (int): Number of stations skipped by this run
        "vehicle_position" (dict[str, str | int | datetime] | None): TODO
        "vehicle_descriptor" (dict[str, str | bool] | None): TODO
        "geopath" (list[dict[str, str | int | list[str]]]): The route's geometry as a sequence of coordinates

        :param run_ref: The run identifier
        :param route_type: Not used (but see overloaded variant)
        :param expand: Optional data to include in returned list
        :param date: Return only data from the specified date
        :param include_geopath: Include the run's geopath data (server default: false)
        :return: A list of records containing the aforementioned fields
        """

        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if type(date) is str:
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("expand", expand, "include_geopath", include_geopath, "date_utc", date.astimezone(timezone.utc).isoformat(), s=req)

        res = self.call(req)["runs"]

        for record in res:
            if record["vehicle_position"] is not None:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]).astimezone(TZ_MELBOURNE) if record["vehicle_position"]["datetime_utc"] is not None else None
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]).astimezone(TZ_MELBOURNE) if record["vehicle_position"]["expiry_time"] is not None else None

        return res

    def list_runs(self: Self,
                  route_id: int,
                  route_type: RouteType | None = None,
                  expand: ExpandType | Iterable[ExpandType] = NONE,
                  date: datetime | str | None = None
                  ) -> list[_Run]:
        """Returns a list of all runs for the specified route ID and, if provided, the specified route type.

        Returned records contain these fields:
        "run_id" (int): Run identifier (deprecated)
        "run_ref" (str): Run identifier
        "route_id" (int): Route identifier
        "route_type" (int): Travel mode identifier
        "final_stop_id" (int): Identifier of final stop on run
        "destination_name" (str): Destination label
        "status" (str): Current status of run (i.e. whether the service is on time, delayed, etc.); "scheduled" if status unavailable
        "direction_id" (int): Travel direction identifier
        "run_sequence" (int): Sort key used to arrange this stop in chronological order in a list of runs on this route
        "express_stop_count" (int): Number of stations skipped by this run
        "vehicle_position" (dict[str, str | int | datetime] | None): TODO
        "vehicle_descriptor" (dict[str, str | bool] | None): TODO
        "geopath" (list[dict[str, str | int | list[str]]]): The route's geometry as a sequence of coordinates

        :param route_id: The route ID number
        :param route_type: The route type of the specified route
        :param expand: Optional data to include in returned list
        :param date: Return only data from the specified date
        :return: A list of records containing the aforementioned fields
        """

        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("expand", expand, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, s=req)

        res = self.call(req)["runs"]
        for record in res:
            if record["vehicle_position"] is not None:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]).astimezone(TZ_MELBOURNE) if record["vehicle_position"]["datetime_utc"] is not None else None
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]).astimezone(TZ_MELBOURNE) if record["vehicle_position"]["expiry_time"] is not None else None

        return res

    def get_stop(self: Self,
                 stop_id: int,
                 route_type: RouteType,
                 stop_location: bool | None = None,
                 stop_amenities: bool | None = None,
                 stop_accessibility: bool | None = None,
                 stop_contact: bool | None = None,
                 stop_ticket: bool | None = None,
                 gtfs: bool | None = None,
                 stop_staffing: bool | None = None,
                 stop_disruptions: bool | None = None
                 ):
        """


        :param stop_id:
        :param route_type:
        :param stop_location:
        :param stop_amenities:
        :param stop_accessibility:
        :param stop_contact:
        :param stop_ticket:
        :param gtfs:
        :param stop_staffing:
        :param stop_disruptions:
        :return:
        """

        req = f"/v3/stops/{stop_id}/route_type/{route_type}"
        req = self.build_arg_string("stop_location", stop_location, "stop_amenities", stop_amenities, "stop_accessibility", stop_accessibility, "stop_contact", stop_contact, "stop_ticket", stop_ticket, "gtfs", gtfs, "stop_staffing", stop_staffing, "stop_disruptions", stop_disruptions, s=req)

        res = self.call(req)
        return res

    def list_stops(self: Self,
                   route_id: int,
                   route_type: RouteType,
                   direction_id: int | None = None,
                   stop_disruptions: bool | None = None
                   ) -> list[_Stop]:
        """Returns a list of all stops on the specified route.

        Returned records contain these fields:
        "disruption_ids" (list[int]): List of disruption identifiers related to this stop
        "stop_suburb" (str): Locality of stop
        "route_type" (int): Transport mode identifier
        "stop_latitude" (float): Stop location's latitude coordinate
        "stop_longitude" (float): Stop location's longitude coordinate
        "stop_sequence" (int): Sort key used to arrange this stop in a list of stops on this route sequentially
        "stop_ticket" (dict[str, str | bool | list[int]]): Ticketing information for this stop
        "stop_id" (int): Stop identifier
        "stop_name" (str): Stop label
        "stop_landmark" (str): Description of nearby significant landmark(s)

        :param route_id: The route ID number
        :param route_type: The route type of the specified route
        :param direction_id: Specify a direction ID number to include stop sequence information in the list
        :param stop_disruptions: Whether to include stop disruption information
        :return: A list of records containing the aforementioned fields
        """

        req = f"/v3/stops/route/{route_id}/route_type/{route_type}"
        req = self.build_arg_string("direction_id", direction_id, "stop_disruptions", stop_disruptions, s=req)
        return self.call(req)["stops"]

    def list_stops_by_location(self: Self,
                               latitude: float,
                               longitude: float,
                               route_types: Iterable[RouteType] | None = None,
                               max_results: int | None = None,
                               max_distance: float | None = None,
                               stop_disruptions: bool | None = None
                               ):
        """


        :param latitude:
        :param longitude:
        :param route_types:
        :param max_results:
        :param max_distance:
        :param stop_disruptions:
        :return:
        """

        req = f"/v3/stops/location/{latitude},{longitude}"
        req = self.build_arg_string("route_types", route_types, "max_results", max_results, "max_distance", max_distance, stop_disruptions, "true" if stop_disruptions else None, s=req)

        res = self.call(req)
        return res

    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int,
                        route_id: int | None = None,
                        platform_numbers: Iterable[str | int] | None = None,
                        direction_id: int | None = None,
                        include_advertised_interchange: bool | None = None,
                        date: datetime | str | None = None,
                        max_results: int | None = None,
                        include_cancelled: bool | None = None,
                        look_backwards: bool | None = None,
                        expand: Iterable[ExpandType] | ExpandType = NONE,
                        include_geopath: bool | None = None
                        ) -> DeparturesResponse:
        """
        Returns a list of departures from the specified stop.

        :param route_type: Transport mode identifier
        :param stop_id: Stop identifier
        :param route_id: If specified, show only departures for the specified route. Only one of 'route_id' and 'platform_numbers' should be specified.
        :param platform_numbers: If specified, show only departures from the specified platform numbers. Only one of 'route_id' and 'platform_numbers' should be specified.
        :param direction_id: If specified, show only departures travelling towards the specified direction
        :param include_advertised_interchange: Whether to include stop interchange information in result
        :param date: If specified, show departures from the specified date and time. If 'look_backwards' is True, show departures that arrive at their terminating destinations prior to the specified date and time instead. Defaults to UTC if timezone not specified
        :param max_results: Return only this number of departures
        :param include_cancelled: Whether to include departures that are cancelled
        :param look_backwards: If set to True, departures that arrive at their terminating destinations prior to the date and time specified in 'date' are returned instead
        :param expand: TODO
        :param include_geopath: Whether to include route geometry data
        :return:
        """

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = f"/v3/departures/route_type/{route_type}/stop/{stop_id}" + (f"/route/{route_id}" if route_id is not None else "")
        req = self.build_arg_string("platform_numbers", platform_numbers, "direction_id", direction_id, "include_advertised_interchange", "true" if include_advertised_interchange else None, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "max_results", max_results, "include_cancelled", "true" if include_cancelled else None, "look_backwards", "true" if look_backwards else None, "expand", expand, "include_geopath", "true" if include_geopath else None, s=req)

        res: dict = self.call(req)
        res["stops"] = {int(key): Stop(**value) for key, value in res["stops"].items()}
        res["routes"] = {int(key): Route(**value) for key, value in res["routes"].items()}
        res["runs"] = {key: Run(**value) for key, value in res["runs"].items()}
        res["directions"] = {int(key): Direction(**value) for key, value in res["directions"].items()}
        res["disruptions"] = {int(key): Disruption(**value) for key, value in res["disruptions"].items()}

        return res  # TODO

    @overload
    def list_disruptions(self: Self,
                         *,
                         route_types: Iterable[RouteType] | None = None,
                         disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | None = None,
                         disruption_status: Literal["current", "planned"] | None = None
                         ):
        """
        Returns a list of all disruptions.

        :param route_types: If specified, list only disruptions for the specified travel modes
        :param disruption_modes: If specified, list only disruptions for the specified disruption modes
        :param disruption_status: If specified, list only disruptions with the specified status
        :return:
        """
        ...

    @overload
    def list_disruptions(self: Self,
                         route_id: int | None = None,
                         stop_id: int | None = None,
                         *,
                         disruption_status: Literal["current", "planned"] | None = None
                         ):
        """
        Returns a list of all disruptions for the specified route and/or stop.

        :param route_id: If route identifier is specified, list only disruptions for the specified route. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param stop_id: If stop identifier is specified, list only disruptions for the specified stop. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param disruption_status: If specified, list only disruptions with the specified status
        :return:
        """
        ...

    def list_disruptions(self: Self,
                         route_id: int | None = None,
                         stop_id: int | None = None,
                         *,
                         route_types: Iterable[RouteType] | None = None,
                         disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | None = None,
                         disruption_status: Literal["current", "planned"] | None = None
                         ):
        """
        Returns a list of all disruptions or, if specified, the disruptions for the specified route and/or stop.

        :param route_id: If route identifier is specified, list only disruptions for the specified route. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param stop_id: If stop identifier is specified, list only disruptions for the specified stop. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param route_types: If specified, list only disruptions for the specified travel modes
        :param disruption_modes: If specified, list only disruptions for the specified disruption modes
        :param disruption_status: If specified, list only disruptions with the specified status
        :return:
        """

        req = "/v3/disruptions" + (f"/route/{route_id}" if route_id is not None else "") + (f"/stop/{stop_id}" if stop_id is not None else "")
        req = self.build_arg_string("route_types", route_types, "disruption_modes", disruption_modes, "disruption_status", disruption_status, s=req)

        res: dict = self.call(req)
        return res

    def get_disruption(self: Self, disruption_id: int):
        """
        Retrieves the details of the disruption with the specified disruption identifier

        :param disruption_id: Disruption identifier
        :return:
        """

        res: dict = self.call(f"/v3/disruptions/{disruption_id}")
        return res

    def list_disruption_modes(self: Self):
        """
        Returns the names and identifiers of all disruption modes.

        :return:
        """

        res: dict = self.call("/v3/disruptions/modes")
        return res

    def fare_estimate(self: Self,
                      zone_a: int,
                      zone_b: int,
                      touch_on: datetime | str | None = None,
                      touch_off: datetime | str | None = None,
                      is_free_tram_zone: bool | None = None,
                      route_types: Iterable[RouteType] | None = None
                      ):
        """
        Returns the estimated fare for the specified journey details.

        :param zone_a:
        :param zone_b:
        :param touch_on:
        :param touch_off:
        :param is_free_tram_zone:
        :param route_types:
        :return:
        """

        if type(touch_on) is str:
            touch_on = datetime.fromisoformat(touch_on)
        if touch_on is not None and touch_on.tzinfo is None:
            touch_on = touch_on.replace(tzinfo=timezone.utc)
        if type(touch_off) is str:
            touch_off = datetime.fromisoformat(touch_off)
        if touch_off is not None and touch_off.tzinfo is None:
            touch_off = touch_off.replace(tzinfo=timezone.utc)

        req = f"/v3/fare_estimate/min_zone/{min(zone_a, zone_b)}/max_zone/{max(zone_a, zone_b)}"
        req = self.build_arg_string("touch_on", touch_on.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_on is not None else None, "touch_off", touch_off.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_off is not None else None, is_free_tram_zone, "true" if is_free_tram_zone else None, "route_types", route_types, s=req)

        res = self.call(req)
        return res

    @overload
    def list_outlets(self: Self,
                     *,
                     max_results: int | None = None
                     ):
        ...

    @overload
    def list_outlets(self: Self,
                     latitude: float,
                     longitude: float,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ):
        ...

    def list_outlets(self: Self,
                     latitude: float | None = None,
                     longitude: float | None = None,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ):
        """


        :param latitude:
        :param longitude:
        :param max_distance:
        :param max_results:
        :return:
        """

        req = "/v3/outlets" + (f"/location/{latitude},{longitude}" if latitude is not None and longitude is not None else "")
        req = self.build_arg_string("max_distance", max_distance, "max_results", max_results, s=req)

        res = self.call(req)
        return res

    @overload
    def search(self: Self,
               search_term: str,
               route_types: Iterable[RouteType] | None = None,
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
               route_types: Iterable[RouteType] | None,
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
               route_types: Iterable[RouteType] | None = None,
               latitude: float | None = None,
               longitude: float | None = None,
               max_distance: float | None = None,
               include_outlets: bool | None = None,
               match_stop_by_suburb: bool | None = None,
               match_route_by_suburb: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ):
        """


        :param search_term:
        :param route_types:
        :param latitude:
        :param longitude:
        :param max_distance:
        :param include_outlets: server default true
        :param match_stop_by_suburb: server default true
        :param match_route_by_suburb: server default true
        :param match_stop_by_gtfs_stop_id: server default false
        :return:
        """

        req = f"/v3/search/{search_term}"
        req = self.build_arg_string("route_types", route_types, "latitude", latitude, "longitude", longitude, "max_distance", max_distance, "include_outlets", include_outlets, "match_stop_by_suburb", match_stop_by_suburb, "match_route_by_suburb", match_route_by_suburb, "match_stop_by_gtfs_stop_id", match_stop_by_gtfs_stop_id, s=req)

        res = self.call(req)
        return res


# Thanks to Lucas Martin-King for providing the general idea for the following code
# https://github.com/lmartinking/melbourne-tramtracker/
class TramTrackerInterface:
    """Interface class with the TramTracker PIDS Web Service."""

    _NAMESPACES: Final[dict[str, str]] = {"soap": "http://www.w3.org/2003/05/soap-envelope", "tramtracker": "http://www.yarratrams.com.au/pidsservice/"}
    CLIENT_TYPE: Final[str] = "WEBPID"
    CLIENT_VERSION: Final[str] = "0.1"
    CLIENT_WEB_SERVICE_VERSION: Final[str] = "6.4.0.0"

    def __init__(self, uuid: str | None = None) -> None:
        """
        Creates a TramTrackerInterface instance, requesting a new UUID from the service if one is not provided.

        :param uuid: The UUID for client authentication, or None to request one from the service
        :return: None
        """
        if type(uuid) not in (str, type(None)):
            raise TypeError("UUID must be str or None")
        if uuid is not None and UUID_PATTERN.fullmatch(uuid) is None:
            raise ValueError("Invalid UUID - UUIDs must take the form 00000000-0000-0000-0000-000000000000")
        self.uuid: Final[str] = self._get_new_uuid() if uuid is None else uuid
        return

    @classmethod
    @sleep_and_retry
    @limits(calls=1, period=30)
    def _post(cls: Self, data: str) -> str:
        """
        Send the specified data to the service, appending the necessary HTTP and XML headers.

        :param data: The data to send
        :return: The response from the service
        """
        print(data, file=stderr)
        r = requests.post(url="http://webpids.tramtracker.com.au/pidsservice/pids.asmx", data=f"<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap=\"http://www.w3.org/2003/05/soap-envelope\">{data}</soap:Envelope>", headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text

    @classmethod
    def _get_new_uuid(cls: Self) -> str:
        """
        Request a new UUID for client identification from the service. Raises a ConnectionError if an unexpected response is received.

        :return: The new UUID
        """
        r = cls._post("<soap:Body><GetNewClientGuid xmlns=\"http://www.yarratrams.com.au/pidsservice/\" /><soap:Body />")
        tree: Element = XML(r)
        result = tree.find("./soap:Body/tramtracker:GetNewClientGuidResponse/tramtracker:GetNewClientGuidResult", cls._NAMESPACES)
        if result is None:
            raise ConnectionError("Service error: service responded successfully but did not return a UUID; check with developer")
        if UUID_PATTERN.fullmatch(result.text) is None:
            raise ConnectionError(f"Service error: service responded successfully but returned an unexpected value: \"{result.text}\"; check with developer")
        return result.text

    def _call(self: Self, request: str) -> str:
        """
        Make the request to the web service, appending the necessary headers to the request.

        :param request: XML request string
        :return: Result of request
        """
        return self._post(f"<soap:Header><PidsClientHeader xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><ClientGuid>{self.uuid}</ClientGuid><ClientType>{self.CLIENT_TYPE}</ClientType><ClientVersion>{self.CLIENT_VERSION}</ClientVersion><ClientWebServiceVersion>{self.CLIENT_WEB_SERVICE_VERSION}</ClientWebServiceVersion></PidsClientHeader></soap:Header><soap:Body>{request}</soap:Body>")

    def list_destinations(self: Self):
        self._call("<GetDestinationsForAllRoutes xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")

    def get_destinations(self: Self, route: str | int):
        self._call(f"<GetDestinationsForRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetDestinationsForRoute>")

    def list_routes(self: Self):
        self._call("<GetMainRoutes xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")

    def list_stops(self: Self, route: str | int) -> list[dict[str, str | int]]:
        response = self._call(f"<GetRouteStopsByRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetRouteStopsByRoute>")
        result: Element = XML(response).find("./soap:Body/tt:GetRouteStopsByRouteResponse/tt:GetRouteStopsByRouteResult/diffgr:diffgram/DocumentElement", namespaces={"soap": "http://www.w3.org/2003/05/soap-envelope", "tt": "http://www.yarratrams.com.au/pidsservice/", "diffgr": "urn:schemas-microsoft-com:xml-diffgram-v1"})

        return [{"tt_id": int(element.find("./TID").text),
                 "stop_name": element.find("./Description").text,
                 "full_stop_name": element.find("./StopName").text,
                 "locality": element.find("./SuburbName").text,
                 "latitude": element.find("./Latitude").text,
                 "longitude": element.find("./Longitude").text
                 } for element in result]

    def get_stop(self: Self, stop_id: int):
        self._call(f"<GetStopInformation xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo></GetStopInformation>")
