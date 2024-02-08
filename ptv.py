from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from hashlib import sha1
from hmac import HMAC
from typing import Any
import requests


class RouteType(Enum):
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

    def __init__(self, dev_id: str | int, key: str) -> None:
        """Initialises a PTVInterface instance with the supplied credentials.

        Parameters:
        devid -- user ID
        key -- API request signing key
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

        Parameters:
        *params -- tuples of (param, value) pairs, or the param and values themselves (must contain the exact number of arguments to complete the URL)
        s -- optionally, the string to append to
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
    
    def _call(self, request: str) -> dict[str, list[dict[str, Any]] | dict[str, Any]]:
        """Make the request to the API and format the result.

        Parameters:
        request -- API request string
        """

        url = self._encode_url(request)
        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        return result
    
    def _encode_url(self, request: str) -> str:
        """Appends the signature and base URL to the request string.
        
        Parameters:
        request -- API request string
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self.devID}"
        signature = HMAC(key=self.key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"
    
    def list_route_types(self) -> list[dict[str, str | int]]:
        """Returns the names and IDs of all route types.

        Returned records contain these fields:
        "route_type_name" : str
        "route_type" : int
        """

        return self._call("/v3/route_types")["route_types"]

    def list_routes(self, route_types: Iterable[RouteType | int] | None = None, route_name: str | None = None) -> list[dict[str, str | int | dict[str, str] | list[dict[str, str | int | list[str]]]]]:
        """Returns all routes of all (or specified) types.

        Parameters:
        route_types -- return only the routes of the specified type(s)
        route_name -- return the routes with names containing the specified substring

        Returned records contain these fields:
        "route_service_status" : dict[str, str]
        "route_type": int
        "route_id": int
        "route_name": str
        "route_number": str
        "route_gtfs_id": str
        "geopath": list[dict[str, str | int | list[str]]]
        """

        req = "/v3/routes"
        if route_types is not None:
            for route_type in route_types:
                req = self._build_arg_string("route_types", route_type.value() if isinstance(route_type, RouteType) else route_type, s=req)
        if route_name is not None:
            req = self._build_arg_string("route_name", route_name, s=req)

        return self._call(req)["route"]

    def get_route(self, route_id: int, include_geopath: bool = False, geopath_utc: str | None = None) -> dict[str, str | int | dict[str, str] | list[dict[str, str | int | list[str]]]]:
        """Returns the details of the route with the specified route ID.

        Parameters:
        route_id -- the route ID number
        include_geopath -- whether to return kif geopath data
        geopath_utc -- ISO 8601 UTC date to filter geopaths by

        Returned record contains these fields:
        "route_service_status": dict[str, str]
        "route_type": int
        "route_id": int
        "route_name": str
        "route_number": str
        "route_gtfs_id": str
        "geopath": list[dict[str, str | int | list[str]]]
        """

        req = f"/v3/routes/{route_id}"
        if include_geopath:
            req = self._build_arg_string("include_geopath", "true", s=req)
        if geopath_utc is not None:
            req = self._build_arg_string("geopath_utc", geopath_utc, s=req)

        return self._call(req)["route"]

    def list_route_directions(self, route_id: int) -> list[dict[str, str | int]]:
        """Returns the directions of travel for a particular route.

        Parameters:
        route_id -- the route ID number

        Returned records contain these fields:
        "route_direction_description": str
        "direction_id": int
        "direction_name": str
        "route_id": int
        "route_type": int
        """

        return self._call(f"/v3/directions/route/{route_id}")["directions"]

    def list_directions(self, direction_id: int, route_type: RouteType | int | None = None) -> list[dict[str, str | int]]:
        """Returns all directions of travel in the database for all (or the specified) route type(s).

        Parameters:
        direction_id -- the direction ID number
        route_type -- return only the directions with the specified route type

        Returned records contain these fields:
        "route_direction_description": str
        "direction_id": int
        "direction_name": str
        "route_id": int
        "route_type": int
        """

        route_type = route_type.value() if isinstance(route_type, RouteType) else route_type
        return self._call(f"/v3/directions/{direction_id}{f"/route_type/{route_type}" if route_type is not None else ""}")["directions"]

    def get_pattern(self, run_ref: str, route_type: RouteType | int, stop_id: int | None = None, date_utc: datetime | str | None = None, include_skipped_stops: bool = False, include_geopath: bool = False) -> list[dict[str, int | str | bool | datetime | list[int] | list[dict[str, int | str]]]]:
        """Returns the stopping pattern of the specified run of the specified route type.

        Parameters:
        run_ref -- the run identifier
        route_type -- the route type of the run
        stop_id -- include only the stop with the specified stop ID
        date_utc --
        include_skipped_stops -- include a list of stops that are skipped by the pattern
        include_geopath -- include the pattern's geopath data

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
        """

        route_type = route_type.value() if isinstance(route_type, RouteType) else route_type
        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"
        req = self._build_arg_string("expand", "None", s=req)

        if stop_id is not None:
            req = self._build_arg_string("stop_id", stop_id, s=req)
        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)
        if include_skipped_stops:
            req = self._build_arg_string("include_skipped_stops", "true", s=req)
        if include_geopath:
            req = self._build_arg_string("include_geopath", "true", s=req)

        res = self._call(req)["departures"]
        for record in res:
            record["scheduled_departure_utc"] = datetime.fromisoformat(record["scheduled_departure_utc"])
            record["estimated_departure_utc"] = datetime.fromisoformat(record["estimated_departure_utc"])
        return res

    def list_runs(self, route_id: int, route_type: RouteType | int | None = None, expand: ExpandType | str | Iterable[ExpandType | str] = ExpandType.NONE, date_utc: datetime | str | None = None) -> list[dict[str, str | int | dict[str, str | int | datetime] | dict[str, str | bool]]]:
        """Returns a list of all runs for the specified route ID and, if provided, the specified route type.

        Parameters:
        route_id -- the route ID number
        route_type -- the route type of the specified route
        expand -- optional data to include in returned list
        date_utc -- return only data from the specified date

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
        "vehicle_description": dict[str, str | bool]
        "geopath": list[dict]
        """

        route_type = route_type.value() if isinstance(route_type, RouteType) else route_type
        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(expand, Iterable):
            for et in expand:
                req = self._build_arg_string("expand", et.value() if isinstance(et, ExpandType) else et, s=req)
        elif expand != ExpandType.NONE:
            req = self._build_arg_string("expand", expand.value() if isinstance(et, ExpandType) else expand, s=req)

        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)

        res = self._call(req)["runs"]
        for record in res:
            if len(record["vehicle_position"]) > 0:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"])
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"])

        return res

    def get_run(self, run_ref: str, route_type: RouteType | int | None = None, expand: ExpandType | str = ExpandType.NONE, date_utc: datetime | str | None = None, include_geopath: bool = False) -> list[dict[str, str | int | dict[str, str | int | datetime] | dict[str, str | bool]]]:
        """Returns a list of all runs for the specified run identifier and, if provided, the specified route type.

        Parameters:
        run_ref -- the run identifier
        route_type -- the route type of the specified run
        expand -- optional data to include in returned list
        date_utc -- return only data from the specified date
        include_geopath -- include the run's geopath data

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
        "vehicle_description": dict[str, str | bool]
        "geopath": list[dict]
        """

        route_type = route_type.value() if isinstance(route_type, RouteType) else route_type
        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(expand, Iterable):
            for et in expand:
                req = self._build_arg_string("expand", et.value() if isinstance(et, ExpandType) else et, s=req)
        elif expand != ExpandType.NONE:
            req = self._build_arg_string("expand", expand.value() if isinstance(et, ExpandType) else expand, s=req)

        if date_utc is not None:
            if isinstance(date_utc, str):
                date_utc = datetime.fromisoformat(date_utc) if "Z" in date_utc else datetime.fromisoformat(date_utc + "Z")
            req = self._build_arg_string("date_utc", date_utc.isoformat(), s=req)

        res = self._call(req)
        res = [res["run"]] if route_type is None else res["runs"]

        for record in res:
            if len(record["vehicle_position"]) > 0:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"])
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"])

        return res

    def list_stops(self, route_id: int, route_type: RouteType | int, direction_id: int | None = None, stop_disruptions: bool = False) -> list[dict[str, str | int | float | dict[str, str | bool | list[int]]]]:
        """Returns a list of all stops on the specified route.

        Parameters:
        route_id -- the route ID number
        route_type -- the route type of the specified route
        direction_id -- specify a direction ID number to include stop sequence information in the list
        stop_disruptions -- whether to include stop disruption information

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
        """

        route_type = route_type.value() if isinstance(route_type, RouteType) else route_type
        req = f"/v3/stops/route/{route_id}/route_type/{route_type}"

        if direction_id is not None:
            req = self._build_arg_string("direction_id", direction_id)
        if stop_disruptions:
            req = self._build_arg_string("stop_disruptions", "true")

        return self._call(req)["stops"]
