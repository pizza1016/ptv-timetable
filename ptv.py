from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from typing import Self, overload
import requests

__all__ = ["PTVInterface", "Mode", "ExpandType"]

type _Values = str | int | float | bool | datetime
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

type _Departure = dict[str, str | int | bool | datetime | list[int] | list[_SkippedStop]]
type _Direction = dict[str, str | int]
type _Geopath = list[dict[str, str | int | list[str]]]
type _Route = dict[str, str | int | dict[str, str] | _Geopath]
type _RouteType = dict[str, str | int]
type _Run = dict[str, str | int | _VehiclePosition | _VehicleDescriptor | _Geopath]
type _SkippedStop = dict[str, str | int]
type _Stop = dict[str, str | int | float | dict[str, str | bool | list[int]]]
type _VehicleDescriptor = dict[str, str | bool]
type _VehiclePosition = dict[str, str | int | datetime]


class Mode(Enum):
    """Contains enum constants to indicate mode of travel."""

    MET_TRAIN = METRO = 0
    TRAM = 1
    BUS = 2
    REG_TRAIN = COACH = VLINE = 3


class ExpandType(Enum):
    ALL = "All"
    STOP = "Stop"
    ROUTE = "Route"
    RUN = "Run"
    DIRECTION = "Direction"
    DISRUPTION = "Disruption"
    VEHICLE_DESCRIPTOR = "VehicleDescriptor"
    VEHICLE_POSITION = "VehiclePosition"
    NONE = "None"
    

class PTVInterface:
    """Interface class with the PTV Timetable API."""

    def __init__(self: Self, dev_id: str | int, key: str) -> None:
        """Initialises a PTVInterface instance with the supplied credentials.

        :param dev_id: User ID
        :param key: API request signing key
        """
        
        if not isinstance(dev_id, (str, int)):
            raise TypeError(f"devID must be type str or int ({type(dev_id)} provided)")
        elif not isinstance(key, str):
            raise TypeError(f"key must be type str ({type(key)} provided)")

        self.devID: str = str(dev_id)
        self.key: bytes = key.encode(encoding="ascii")
        self.last_req = None
        return

    @staticmethod
    def _build_arg_string(*params: tuple[str, str | int] | str | int, s: str = "") -> str:
        """Builds a URL argument string using the specified parameter-value pairs.

        :param params: Tuples of (param, value) pairs, or the param and values themselves (must contain the exact number of arguments to complete the URL)
        :param s: Optionally, the string to append to
        :return: Modified URL string
        """

        i = 0
        while i < len(params):
            if isinstance(params[i], tuple):
                s += f"{"&" if "?" in s else "?"}{params[i][0]}={params[i][1]}"
                i += 1
            elif isinstance(params[i], str):
                if i + 1 >= len(params):
                    raise ValueError(f"Not enough arguments provided (missing value for {params[i]})")
                if not isinstance(params[i + 1], (str, int)):
                    raise TypeError(f"Argument {i + 1} ({params[i + 1]}) is not str or int")
                s += f"{"&" if "?" in s else "?"}{params[i]}={params[i + 1]}"
                i += 2
            else:
                raise TypeError(f"Argument {i} ({params[i]}) is not tuple or str")

        return s

    @sleep_and_retry
    @limits(calls=1, period=5)  # 1 call every 5 seconds
    def _call(self: Self, request: str) -> dict[str, _Record | list[_Record]]:
        """Make the request to the API and format the result.

        :param request: API request string
        :return: Result of API request as a dict
        """

        url = self._encode_url(request)
        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        return result
    
    def _encode_url(self: Self, request: str) -> str:
        """Appends the signature and base URL to the request string.
        
        :param request: API request string
        :return: API request URL
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self.devID}"
        signature = HMAC(key=self.key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

    def list_route_directions(self: Self, route_id: int) -> list[_Direction]:
        """Returns the directions of travel for a particular route.

        Returned records contain these fields:
        "route_direction_description": str
        "direction_id": int
        "direction_name": str
        "route_id": int
        "route_type": int

        :param route_id: The route ID number
        :return: A list of records containing the aforementioned fields
        """

        return self._call(f"/v3/directions/route/{route_id}")["directions"]

    def list_directions(self: Self, direction_id: int, route_type: Mode | int | None = None) -> list[_Direction]:
        """Returns all directions of travel in the database for all (or the specified) route type(s).

        Returned records contain these fields:
        "route_direction_description": str
        "direction_id": int
        "direction_name": str
        "route_id": int
        "route_type": int

        :param direction_id: The direction ID number
        :param route_type: Return only the directions with the specified route type
        :return: A list of records containing the aforementioned fields
        """

        route_type = route_type.value if isinstance(route_type, Mode) else route_type
        return self._call(f"/v3/directions/{direction_id}{f"/route_type/{route_type}" if route_type is not None else ""}")["directions"]

    def get_pattern(self: Self, run_ref: str, route_type: Mode | int, stop_id: int | None = None, date_utc: datetime | str | None = None, include_skipped_stops: bool = False, include_geopath: bool = False) -> list[_Departure]:
        """Returns the stopping pattern of the specified run of the specified route type.

        Returned records contain these fields:
        "skipped_stops": list[dict[str, int | str]]
        "stop_id": int
        "route_id": int
        "run_id": int
        "run_ref": str
        "direction_id": int
        "disruption_ids": list[int]
        "scheduled_departure_utc": datetime
        "estimated_departure_utc": datetime
        "at_platform": bool
        "platform_number": str
        "flags": str
        "departure_sequence": int

        :param run_ref: The run identifier
        :param route_type: The route type of the run
        :param stop_id: Include only the stop with the specified stop ID
        :param date_utc: TODO
        :param include_skipped_stops: Include a list of stops that are skipped by the pattern
        :param include_geopath: Include the pattern's geopath data
        :return: A list of records containing the aforementioned fields
        """

        route_type = route_type.value if isinstance(route_type, Mode) else route_type
        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"
        req = self._build_arg_string("expand", "None", s=req)

        if stop_id is not None:
            req = self._build_arg_string("stop_id", stop_id, s=req)
        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(
                    date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)
        if include_skipped_stops:
            req = self._build_arg_string("include_skipped_stops", "true", s=req)
        if include_geopath:
            req = self._build_arg_string("include_geopath", "true", s=req)

        res = self._call(req)["departures"]
        for record in res:
            record["scheduled_departure_utc"] = datetime.fromisoformat(record["scheduled_departure_utc"]) if record["scheduled_departure_utc"] is not None else None
            record["estimated_departure_utc"] = datetime.fromisoformat(record["estimated_departure_utc"]) if record["estimated_departure_utc"] is not None else None
        return res

    def get_route(self: Self, route_id: int, include_geopath: bool = False, geopath_utc: str | None = None) -> _Route:
        """Returns the details of the route with the specified route ID.

        Returned record contains these fields:
        "route_service_status": dict[str, str]
        "route_type": int
        "route_id": int
        "route_name": str
        "route_number": str
        "route_gtfs_id": str
        "geopath": list[dict[str, str | int | list[str]]]

        :param route_id: The route ID number
        :param include_geopath: Include the route's geopath data
        :param geopath_utc: ISO 8601 UTC date to filter geopaths by
        :return: A record containing the aforementioned fields
        """

        req = f"/v3/routes/{route_id}"
        if include_geopath:
            req = self._build_arg_string("include_geopath", "true", s=req)
        if geopath_utc is not None:
            req = self._build_arg_string("geopath_utc", geopath_utc, s=req)

        return self._call(req)["route"]

    def list_routes(self: Self, route_types: Iterable[Mode | int] | None = None, route_name: str | None = None) -> list[_Route]:
        """Returns all routes of all (or specified) types.

        Returned records contain these fields:
        "route_service_status" : dict[str, str]
        "route_type": int
        "route_id": int
        "route_name": str
        "route_number": str
        "route_gtfs_id": str
        "geopath": list[dict[str, str | int | list[str]]]

        :param route_types: Return only the routes of the specified type(s)
        :param route_name: Return the routes with names containing the specified substring
        :return: A list of records containing the aforementioned fields
        """

        req = "/v3/routes"
        if route_types is not None:
            for route_type in route_types:
                req = self._build_arg_string("route_types", route_type.value if isinstance(route_type, Mode) else route_type, s=req)
        if route_name is not None:
            req = self._build_arg_string("route_name", route_name, s=req)

        return self._call(req)["routes"]

    def list_route_types(self: Self) -> list[_RouteType]:
        """Returns the names and IDs of all route types.

        Returned records contain these fields:
        "route_type_name" : str
        "route_type" : int

        :return: A list of records containing the aforementioned fields
        """

        return self._call("/v3/route_types")["route_types"]

    @overload
    def get_run(self: Self, run_ref: str, route_type: None, expand: ExpandType | str, date_utc: datetime | str, include_geopath: bool) -> list[_Run]:
        """Returns a list of all runs for the specified run identifier.

        Returned records contain these fields:
        "run_id": int
        "run_ref": str
        "route_id": int
        "route_type": int
        "final_stop_id": int
        "destination_name": str
        "status": str
        "direction_id": int
        "run_sequence": int
        "express_stop_count": int
        "vehicle_position": dict[str, str | int | datetime]
        "vehicle_descriptor": dict[str, str | bool]
        "geopath": list[dict[str, str | int | list[str]]]

        :param run_ref: The run identifier
        :param route_type: Not used (but see overloaded variant)
        :param expand: Optional data to include in returned list
        :param date_utc: Return only data from the specified date
        :param include_geopath: Include the run's geopath data
        :return: A list of records containing the aforementioned fields
        """
        ...

    @overload
    def get_run(self: Self, run_ref: str, route_type: Mode | int, expand: ExpandType | str, date_utc: datetime | str, include_geopath: bool) -> _Run:
        """Returns the run with the specified run identifier and route type.

        The returned record contain these fields:
        "run_id": int
        "run_ref": str
        "route_id": int
        "route_type": int
        "final_stop_id": int
        "destination_name": str
        "status": str
        "direction_id": int
        "run_sequence": int
        "express_stop_count": int
        "vehicle_position": dict[str, str | int | datetime]
        "vehicle_descriptor": dict[str, str | bool]
        "geopath": list[dict[str, str | int | list[str]]]

        :param run_ref: The run identifier
        :param route_type: The route type of the specified run
        :param expand: Optional data to include in returned list
        :param date_utc: Return only data from the specified date
        :param include_geopath: Include the run's geopath data
        :return: A record containing the aforementioned fields
        """
        ...

    def get_run(self, run_ref, route_type=None, expand=ExpandType.NONE, date_utc=None, include_geopath=False):
        route_type = route_type.value if isinstance(route_type, Mode) else route_type
        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(expand, Iterable):
            for et in expand:
                req = self._build_arg_string("expand", et.value if isinstance(et, ExpandType) else et, s=req)
        elif expand != ExpandType.NONE:
            req = self._build_arg_string("expand", expand.value if isinstance(expand, ExpandType) else expand, s=req)

        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)

        if include_geopath:
            req = self._build_arg_string("include_geopath", "true", s=req)

        res = self._call(req)
        res = res["run"] if route_type is None else res["runs"]

        if route_type is None:
            for record in res:
                if record["vehicle_position"] is not None:
                    record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]) if record["vehicle_position"]["datetime_utc"] is not None else None
                    record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]) if record["vehicle_position"]["expiry_time"] is not None else None
        else:
            if res["vehicle_position"] is not None:
                res["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(res["vehicle_position"]["datetime_utc"]) if res["vehicle_position"]["datetime_utc"] is not None else None
                res["vehicle_position"]["expiry_time"] = datetime.fromisoformat(res["vehicle_position"]["expiry_time"]) if res["vehicle_position"]["expiry_time"] is not None else None

        return res

    def list_runs(self: Self, route_id: int, route_type: Mode | int | None = None, expand: ExpandType | str | Iterable[ExpandType | str] = ExpandType.NONE, date_utc: datetime | str | None = None) -> list[_Run]:
        """Returns a list of all runs for the specified route ID and, if provided, the specified route type.

        Returned records contain these fields:
        "run_id": int
        "run_ref": str
        "route_id": int
        "route_type": int
        "final_stop_id": int
        "destination_name": str
        "status": str
        "direction_id": int
        "run_sequence": int
        "express_stop_count": int
        "vehicle_position": dict[str, int | str | datetime]
        "vehicle_descriptor": dict[str, str | bool]
        "geopath": list[dict[str, str | int | list[str]]]

        :param route_id: The route ID number
        :param route_type: The route type of the specified route
        :param expand: Optional data to include in returned list
        :param date_utc: Return only data from the specified date
        :return: A list of records containing the aforementioned fields
        """

        route_type = route_type.value if isinstance(route_type, Mode) else route_type
        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(expand, Iterable):
            for et in expand:
                req = self._build_arg_string("expand", et.value if isinstance(et, ExpandType) else et, s=req)
        elif expand != ExpandType.NONE:
            req = self._build_arg_string("expand", expand.value if isinstance(expand, ExpandType) else expand, s=req)

        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)

        res = self._call(req)["runs"]
        for record in res:
            if record["vehicle_position"] is not None:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]) if record["vehicle_position"]["datetime_utc"] is not None else None
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]) if record["vehicle_position"]["expiry_time"] is not None else None

        return res

    def list_stops(self: Self, route_id: int, route_type: Mode | int, direction_id: int | None = None, stop_disruptions: bool = False) -> list[_Stop]:
        """Returns a list of all stops on the specified route.

        Returned records contain these fields:
        "disruption_ids": list[int]
        "stop_suburb": str
        "route_type": int
        "stop_latitude": float
        "stop_longitude": float
        "stop_sequence": int
        "stop_ticket": dict[str, str | bool | list[int]]
        "stop_id": int
        "stop_name": str
        "stop_landmark": str

        :param route_id: The route ID number
        :param route_type: The route type of the specified route
        :param direction_id: Specify a direction ID number to include stop sequence information in the list
        :param stop_disruptions: Whether to include stop disruption information
        :return: A list of records containing the aforementioned fields
        """

        route_type = route_type.value if isinstance(route_type, Mode) else route_type
        req = f"/v3/stops/route/{route_id}/route_type/{route_type}"

        if direction_id is not None:
            req = self._build_arg_string("direction_id", direction_id)
        if stop_disruptions:
            req = self._build_arg_string("stop_disruptions", "true")

        return self._call(req)["stops"]
