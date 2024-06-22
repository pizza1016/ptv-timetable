from datetime import datetime
from defusedxml.ElementTree import XML
from ratelimit import sleep_and_retry, limits
from sys import stderr
from typing import Final, Literal, Self
from xml.etree.ElementTree import Element
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import tzdata

__all__ = ["TramTrackerClient"]

TZ_MELBOURNE = ZoneInfo("Australia/Melbourne")
UUID_PATTERN = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")

logger = logging.getLogger("tramtracker")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(stderr))


# Thanks to Lucas Martin-King for providing the general idea for the following code
# https://github.com/lmartinking/melbourne-tramtracker/
class TramTrackerClient:
    """Interface class with the TramTracker PIDS Web Service."""

    _NAMESPACES: Final[dict[str, str]] = {"soap": "http://www.w3.org/2003/05/soap-envelope", "tramtracker": "http://www.yarratrams.com.au/pidsservice/", "diffgr": "urn:schemas-microsoft-com:xml-diffgram-v1"}
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
        self.uuid: Final[str] = self.get_new_uuid() if uuid is None else uuid
        return

    @classmethod
    @sleep_and_retry
    @limits(calls=1, period=30)
    def _post(cls: Self, data: str) -> str:
        """
        Sends the specified data to the service, appending the necessary HTTP and XML headers.

        :param data: The data to send
        :return: The response from the service
        """
        logger.debug(data)
        r = requests.post(url="http://webpids.tramtracker.com.au/pidsservice/pids.asmx", data=f"<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap=\"http://www.w3.org/2003/05/soap-envelope\">{data}</soap:Envelope>", headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text

    @classmethod
    def get_new_uuid(cls: Self) -> str:
        """
        Requests a new UUID for client identification from the service. Raises a ConnectionError if an unexpected response is received.

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
        Makes the request to the web service, appending the necessary headers to the request.

        :param request: XML request string
        :return: Result of request
        """
        return self._post(f"<soap:Header><PidsClientHeader xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><ClientGuid>{self.uuid}</ClientGuid><ClientType>{self.CLIENT_TYPE}</ClientType><ClientVersion>{self.CLIENT_VERSION}</ClientVersion><ClientWebServiceVersion>{self.CLIENT_WEB_SERVICE_VERSION}</ClientWebServiceVersion></PidsClientHeader></soap:Header><soap:Body>{request}</soap:Body>")

    def list_destinations(self: Self) -> list[dict[str, str | int]]:
        """
        Returns a list of all destinations for the main (i.e. non-altered) routes on the network.

        :return: A list of dicts representing a destination
        """
        response = self._call("<GetDestinationsForAllRoutes xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetDestinationsForAllRoutesResponse/tramtracker:GetDestinationsForAllRoutesResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)
        return [{"route_number": int(element.find("./RouteNo").text),
                 "up_direction": element.find("./UpStop").text == "true",
                 "destination_name": element.find("./Destination").text
                 } for element in result]

    def get_destinations(self: Self, route: str | int) -> dict[str, str]:
        """
        Returns the destinations at the two ends of the specified route.

        :return: A dict containing the destinations in the up and down directions
        """
        response = self._call(f"<GetDestinationsForRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetDestinationsForRoute>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetDestinationsForRouteResponse/tramtracker:GetDestinationsForRouteResult/diffgr:diffgram/DocumentElement/RouteDestinations", namespaces=self._NAMESPACES)
        return {"up_destination": result.find("./UpDestination").text, "down_destination": result.find("./DownDestination").text}

    def list_routes_at_stop(self: Self, stop_id: int) -> list[str]:
        """
        Returns the tram routes that passes through the specified stop.

        :param stop_id: TramTracker code of the stop
        :return: List of tram route numbers
        """
        response = self._call(f"<GetMainRoutesForStop xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo></GetMainRoutesForStop>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetMainRoutesForStopResponse/tramtracker:GetMainRoutesForStopResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)
        return [item.find("./RouteNo").text for item in result]

    def get_tram(self: Self, tram_number: int) -> dict[str, str | int | bool]:
        """
        Returns the route, direction and other details of a tram that is currently in service on the network.

        :param tram_number: The tram vehicle number (printed inside and outside the tram)
        :return: Detailed information about a tram's route
        """
        response = self._call(f"<GetNextPredictedArrivalTimeAtStopsForTramNo xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><tramNo>{tram_number}</tramNo></GetNextPredictedArrivalTimeAtStopsForTramNo>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetNextPredictedArrivalTimeAtStopsForTramNoResponse/tramtracker:GetNextPredictedArrivalTimeAtStopsForTramNoResult/diffgr:diffgram/NewDataSet/TramNoRunDetailsTable", namespaces=self._NAMESPACES)
        return {"tram_number": int(result.find("./VehicleNo").text),
                "at_layover": result.find("./AtLayover").text == "true",
                "available": result.find("./Available").text == "true",
                "route": result.find("./RouteNo").text,
                "headboard_route_number": result.find("./HeadBoardRouteNo").text,
                "up_direction": result.find("./Up").text == "true",
                "has_special_event": result.find("./HasSpecialEvent").text == "true",
                "has_disruption": result.find("./HasDisruption").text == "true"
                }

    def next_trams(self: Self, stop_id: int, route: str | int = 0, low_floor: bool = False) -> list[dict[str, str | int | bool | datetime]]:
        """
        Returns the arrival times of the next four trams predicted to arrive at the specified stop.

        :param stop_id: TramTracker code of the stop
        :param route: If specified, returns arrivals for the specified route only; 0 (default) returns arrivals for all routes
        :param low_floor: If True, returns arrivals with low-floor trams only
        """
        response = self._call(f"<GetNextPredictedRoutesCollection xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo><routeNo>{route}</routeNo><lowFloor>{"true" if low_floor else "false"}</lowFloor></GetNextPredictedRoutesCollection>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetNextPredictedRoutesCollectionResponse/tramtracker:GetNextPredictedRoutesCollectionResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)

        return [{"internal_route_number": int(element.find("./InternalRouteNo").text),
                 "route": element.find("./RouteNo").text,
                 "headboard_route_number": element.find("./HeadboardRouteNo").text,
                 "tram_number": int(element.find("./VehicleNo").text),
                 "destination": element.find("./Destination").text,
                 "has_disruption": element.find("./HasDisruption").text == "true",
                 "tt_available": element.find("./IsTTAvailable").text == "true",
                 "low_floor_tram": element.find("./IsLowFloorTram").text == "true",
                 "air_conditioned": element.find("./AirConditioned").text == "true",
                 "display_ac": element.find("./DisplayAC").text == "true",
                 "has_special_event": element.find("./HasSpecialEvent").text == "true",
                 "estimated_arrival": datetime.fromisoformat(element.find("./PredictedArrivalDateTime").text).astimezone(TZ_MELBOURNE),
                 "request_time": datetime.fromisoformat(element.find("./RequestDateTime").text).astimezone(TZ_MELBOURNE)
                 } for element in result]

    # API not currently working
    # def list_platform_stops(self: Self, route: str | int, up_direction: bool):
    #     """
    #     Returns a list of stops with raised platforms and step-free access with compatible trams along the specified route and direction.
    #
    #     :param route: The route number
    #     :param up_direction: Set to True to get stops in the "up" direction, or False to get stops in the "down" direction, as described by list_destinations() and get_destinations()
    #     :return: A list of stops
    #     """
    #     response = self._call(f"<GetPlatformStopsByRouteAndDirection xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo><isUpDirection>{str(up_direction).lower()}</isUpDirection></GetPlatformStopsByRouteAndDirection>")
    #     result: Element = XML(response).find("./soap:Body/tramtracker:GetPlatformStopsByRouteAndDirectionResponse/tramtracker:GetPlatformStopsByRouteAndDirectionResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)

    def list_stops(self: Self, route: str | int) -> list[dict[str, str | int]]:
        """
        Returns a list of stops along the specified route.

        :param route: Route number of the route to list stops for
        :return: List of dicts containing details of each stop on the route
        """
        response = self._call(f"<GetRouteStopsByRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetRouteStopsByRoute>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetRouteStopsByRouteResponse/tramtracker:GetRouteStopsByRouteResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)

        return [{"tt_id": int(element.find("./TID").text),
                 "stop_name": element.find("./Description").text,
                 "full_stop_name": element.find("./StopName").text,
                 "locality": element.find("./SuburbName").text,
                 "latitude": element.find("./Latitude").text,
                 "longitude": element.find("./Longitude").text,
                 "up_direction": element.find("./UpStop").text == "true",
                 "in_city": element.find("./IsCityStop").text == "true",
                 "platform_stop": element.find("./IsPlatformStop").text == "true",
                 "platform_length": element.find("./StopLength").text,
                 "connecting_buses": element.find("./HasConnectingBuses").text == "true",
                 "connecting_trains": element.find("./HasConnectingTrains").text == "true",
                 "connecting_trams": element.find("./HasConnectingTrams").text == "true",
                 "stop_sequence": element.find("./StopSequence")
                 } for element in result]

    def list_routes(self: Self) -> list[dict[str, str | int | bool | datetime]]:
        """
        Returns all tram routes on the network.

        :return: List of tram routes and their details
        """
        response = self._call("<GetRouteSummaries xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetRouteSummariesResponse/tramtracker:GetRouteSummariesResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)
        return [{"route": element.find("./RouteNo").text,
                 "headboard_route_number": element.find("./HeadboardRouteNo").text,
                 "internal_route_number": int(element.find("./InternalRouteNo").text),
                 "is_main_route": element.find("./IsMainRoute").text == "1",
                 "main_route_number": element.find("./MainRouteNo").text,
                 "description": element.find("./Description").text,
                 "up_destination": element.find("./UpDestination").text,
                 "down_destination": element.find("./DownDestination").text,
                 "has_low_floor": element.find("./HasLowFloor").text == "true",
                 "last_modified": datetime.fromisoformat(element.find("./LastModified").text).astimezone(TZ_MELBOURNE)
                 } for element in result]

    def get_schedules_collection(self: Self, stop_id: int, route: str | int = 0, low_floor: bool = False, request_time: datetime | str = datetime.now(TZ_MELBOURNE)) -> list[dict[str, str | int | bool | datetime | None]]:
        """
        Returns the details of the three services scheduled to arrive at the specified stop on or after the date & time specified in request_time (which defaults to the current system time). Unlike next_trams(), this *apparently* goes by the scheduled time, rather than real time.

        :param stop_id: TramTracker code of the stop
        :param route: If specified, returns arrivals for the specified route only; 0 (default) returns arrivals for all routes
        :param low_floor: If True, returns arrivals with low-floor trams only
        :param request_time: Date & time at which to retrieve services for, either using a datetime object, or a str in ISO 8601 format. Assumes Melbourne time zone if unspecified. Defaults to current system time
        :return: List containing details of three services
        """
        if isinstance(request_time, str):
            request_time = datetime.fromisoformat(request_time)
        if request_time.tzinfo is None:
            request_time = request_time.replace(tzinfo=TZ_MELBOURNE)

        response = self._call(f"<GetSchedulesCollection xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo><routeNo>{route}</routeNo><lowFloor>{"true" if low_floor else "false"}</lowFloor><clientRequestDateTime>{request_time.isoformat()}</clientRequestDateTime></GetSchedulesCollection>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetSchedulesCollectionResponse/tramtracker:GetSchedulesCollectionResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)

        return [{"prediction_type": int(element.find("./PredictionType").text),
                 "trip_id": int(element.find("./TripID").text),
                 "route_id": int(element.find("./InternalRouteNo").text),
                 "route": element.find("./RouteNo").text,
                 "headboard_route_number": element.find("./HeadboardRouteNo").text,
                 "tram_number": int(element.find("./VehicleNo").text),
                 "destination": element.find("./Destination").text,
                 "has_disruption": element.find("./HasDisruption").text == "true",
                 "tt_available": element.find("./IsTTAvailable").text == "true",
                 "low_floor_tram": element.find("./IsLowFloorTram").text == "true",
                 "air_conditioned": element.find("./AirConditioned").text == "true",
                 "display_ac": element.find("./DisplayAC").text == "true",
                 "has_special_event": element.find("./HasSpecialEvent").text == "true",
                 "special_event_message": element.find("./SpecialEventMessage").text,
                 "estimated_arrival": datetime.fromisoformat(element.find("./PredictedArrivalDateTime").text).astimezone(TZ_MELBOURNE),
                 "request_time": datetime.fromisoformat(element.find("./RequestDateTime").text).astimezone(TZ_MELBOURNE)
                 } for element in result]

    def get_schedules_for_trip(self: Self, trip_id: int, scheduled_arrival: datetime | str) -> list[dict[str, int | datetime]]:
        """
        Returns a list of the stops made by the specified trip and the times of arrival at each stop.

        :param trip_id: Trip identifier retrieved from get_schedules_collection()
        :param scheduled_arrival: The date, as a datetime object or a str in ISO 8601 format, on which the service operates and for which the API should return the arrival times for. Time fields are ignored by the API
        :return: A list of stops, in sequential stop order
        """
        if isinstance(scheduled_arrival, str):
            scheduled_arrival = datetime.fromisoformat(scheduled_arrival)
        if scheduled_arrival.tzinfo is None:
            scheduled_arrival = scheduled_arrival.replace(tzinfo=TZ_MELBOURNE)

        response = self._call(f"<GetSchedulesForTrip xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><tripID>{trip_id}</tripID><scheduledDateTime>{scheduled_arrival.isoformat()}</scheduledDateTime></GetSchedulesForTrip>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetSchedulesForTripResponse/tramtracker:GetSchedulesForTripResult/diffgr:diffgram/DocumentElement", namespaces=self._NAMESPACES)

        return [{"stop_id": int(element.find("./StopNo").text),
                 "time": int(element.find("./Time").text),
                 "scheduled_arrival": datetime.fromisoformat(element.find("./ScheduledArrivalDateTime").text).astimezone(TZ_MELBOURNE)
                 } for element in result]

    # API not currently working
    # def get_stop(self: Self, stop_id: int):
    #     response = self._call(f"<GetStopInformation xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo></GetStopInformation>")

    def get_data_updates(self: Self, since: datetime | str) -> tuple[list[dict[str, str | int | bool | Literal["UPDATE", "DELETE"]]], list[dict[str, int | Literal["UPDATE", "DELETE"]]], datetime]:
        """
        Returns details of the changes to routes and stops between the time specified in 'since' and now.

        :param since: Date & time at which to get changes from, either using a datetime object, or a str in ISO 8601 format. Assumes Melbourne time zone if unspecified
        :return: A 3-tuple containing a list of changed routes, a list of changed stops, and the API server's system time
        """
        if isinstance(since, str):
            since = datetime.fromisoformat(since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=TZ_MELBOURNE)

        response = self._call(f"<GetStopsAndRoutesUpdatesSince xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><dateSince>{since.isoformat()}</dateSince></GetStopsAndRoutesUpdatesSince>")
        result: Element = XML(response).find("./soap:Body/tramtracker:GetStopsAndRoutesUpdatesSinceResponse/tramtracker:GetStopsAndRoutesUpdatesSinceResult/diffgr:diffgram/dsCoreDataChanges", namespaces=self._NAMESPACES)

        routes = []
        stops = []
        server_time = None
        for element in result:
            if element.tag == "dtRoutesChanges":
                routes.append({"route_id": int(element.find("./ID").text),
                               "headboard_route_number": element.find("./HeadboardRouteNo").text,
                               "route": element.find("./RouteNo").text,
                               "is_main_route": element.find("./IsMainRoute").text == "true",
                               "action": element.find("./Action").text,
                               "colour": element.find("./Colour").text
                               })
            elif element.tag == "dtStopsChanges":
                stops.append({"stop_id": int(element.find("./StopNo").text),
                              "action": element.find("./Action").text
                              })
            elif element.tag == "dtServerTime":
                if server_time is None:
                    server_time = datetime.fromisoformat(element.find("./ServerTime").text).astimezone(TZ_MELBOURNE)
                else:
                    logger.warning("server_time already provided", stack_info=True)
            else:
                logger.warning(f"Unexpected tag: {element.tag}", stack_info=True)

        return routes, stops, server_time
