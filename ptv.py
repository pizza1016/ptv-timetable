from collections.abc import Iterable
from datetime import datetime, timezone
from defusedxml.ElementTree import XML
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from sys import stderr
from typing import Final, Literal, Self
from xml.etree.ElementTree import Element
import re
import requests

__all__ = ["PTVInterface", "TramTrackerInterface", "MET_TRAIN", "METRO", "TRAM", "BUS", "REG_TRAIN", "COACH", "VLINE", "ALL", "STOP", "ROUTE", "RUN", "DIRECTION", "DISRUPTION", "VEHICLE_DESCRIPTOR", "VEHICLE_POSITION", "NONE"]

type _Values = str | int | float | bool | datetime
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

type _Departure = dict[str, str | int | bool | datetime | list[int] | list[_SkippedStop]]
type _Direction = dict[str, str | int]
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
    

class PTVInterface:
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
        r = requests.get(url)
        r.raise_for_status()
        result = r.json()
        return result
    
    def _encode_url(self: Self, request: str) -> str:
        """Appends the signature and base URL to the request string.
        
        :param request: API request string
        :return: API request URL
        """

        raw = f"{request}{"&" if "?" in request else "?"}devid={self._devID}"
        signature = HMAC(key=self._key, msg=raw.encode(encoding="ascii"), digestmod=sha1).hexdigest()
        return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

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

    def get_pattern(self: Self, run_ref: str, route_type: RouteType, stop_id: int | None = None, date: datetime | str | None = None, include_skipped_stops: bool = False, expand: ExpandType | Iterable[ExpandType] = NONE, include_geopath: bool = False) -> list[_Departure]:
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
            date = datetime(date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond, timezone.utc)

        req = self.build_arg_string("stop_id", stop_id, "date_utc", date.isoformat(), "include_skipped_stops", "true" if include_skipped_stops else None, "expand", expand, "include_geopath", "true" if include_geopath else None, s=req)

        res = self.call(req)["departures"]
        for record in res:
            record["scheduled_departure_utc"] = datetime.fromisoformat(record["scheduled_departure_utc"]) if record["scheduled_departure_utc"] is not None else None
            record["estimated_departure_utc"] = datetime.fromisoformat(record["estimated_departure_utc"]) if record["estimated_departure_utc"] is not None else None
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
        """Returns the names and IDs of all route types.

        Returned records contain these fields:
        "route_type_name" (str):
        "route_type" (int):

        :return: A list of records containing the aforementioned fields
        """

        return self.call("/v3/route_types")["route_types"]

    def get_run(self: Self, run_ref: str, route_type: RouteType | None = None, expand: ExpandType = NONE, date: datetime | str | None = None, include_geopath: bool = False) -> list[_Run]:
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
        :param include_geopath: Include the run's geopath data
        :return: A list of records containing the aforementioned fields
        """

        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date.tzinfo is None:
            date = datetime(date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond, timezone.utc)

        req = self.build_arg_string("expand", expand, "include_geopath", "true" if include_geopath else None, "date_utc", date.isoformat(), s=req)

        res = self.call(req)["runs"]

        for record in res:
            if record["vehicle_position"] is not None:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]) if record["vehicle_position"]["datetime_utc"] is not None else None
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]) if record["vehicle_position"]["expiry_time"] is not None else None

        return res

    def list_runs(self: Self, route_id: int, route_type: RouteType | None = None, expand: ExpandType | Iterable[ExpandType] = NONE, date: datetime | str | None = None) -> list[_Run]:
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
        if date.tzinfo is None:
            date = datetime(date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond, timezone.utc)

        req = self.build_arg_string("expand", expand, "date_utc", date.isoformat(), s=req)

        res = self.call(req)["runs"]
        for record in res:
            if record["vehicle_position"] is not None:
                record["vehicle_position"]["datetime_utc"] = datetime.fromisoformat(record["vehicle_position"]["datetime_utc"]) if record["vehicle_position"]["datetime_utc"] is not None else None
                record["vehicle_position"]["expiry_time"] = datetime.fromisoformat(record["vehicle_position"]["expiry_time"]) if record["vehicle_position"]["expiry_time"] is not None else None

        return res

    def list_stops(self: Self, route_id: int, route_type: RouteType, direction_id: int | None = None, stop_disruptions: bool = False) -> list[_Stop]:
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
        req = self.build_arg_string("direction_id", direction_id, "stop_disruptions", "true" if stop_disruptions else None, s=req)
        return self.call(req)["stops"]

    def list_departures(self, route_type: RouteType, stop_id: int, route_id: int | None = None, platform_numbers: Iterable[str | int] | None = None, direction_id: int | None = None, include_advertised_interchange: bool = False, date: datetime | str | None = None, max_results: int | None = None, include_cancelled: bool = False, look_backwards: bool = False, expand: Iterable[ExpandType] | ExpandType = NONE, include_geopath: bool = False) -> list[_Departure]:
        """


        :param route_type:
        :param stop_id:
        :param route_id:
        :param platform_numbers:
        :param direction_id:
        :param include_advertised_interchange:
        :param date:
        :param max_results:
        :param include_cancelled:
        :param look_backwards:
        :param expand:
        :param include_geopath:
        :return:
        """

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date.tzinfo is None:
            date = datetime(date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond, timezone.utc)

        req = f"/v3/departures/route_type/{route_type}/stop/{stop_id}" + (f"/route/{route_id}" if route_id is not None else "")
        req = self.build_arg_string("platform_numbers", platform_numbers, "direction_id", direction_id, "include_advertised_interchange", "true" if include_advertised_interchange else None, "date_utc", date.isoformat(), "max_results", max_results, "include_cancelled", "true" if include_cancelled else None, "look_backwards", "true" if look_backwards else None, "expand", expand, "include_geopath", "true" if include_geopath else None, s=req)

        res = self.call(req)

        return res["departures"]


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
        return [{"tt_id": int(element.find("./TID").text), "stop_name": element.find("./Description").text, "full_stop_name": element.find("./StopName").text, "locality": element.find("./SuburbName").text, "latitude": element.find("./Latitude").text, "longitude": element.find("./Longitude").text} for element in result]

    def get_stop(self: Self, stop_id: int):
        self._call(f"<GetStopInformation xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo></GetStopInformation>")
