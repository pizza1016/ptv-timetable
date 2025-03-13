from collections.abc import Callable
from aiohttp.client import ClientSession
from aiolimiter.leakybucket import AsyncLimiter
from datetime import datetime, timedelta, timezone
from typing import Final, Self
from zoneinfo import ZoneInfo
import logging
import platform
if platform.system() == "Windows":
    import tzdata

from .types import *

__all__ = ["AsyncTramTrackerAPI"]

_logger: Final = logging.getLogger("ptv-timetable.tramtracker.asyncapi")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


class AsyncTramTrackerAPI(object):
    """Interface class for the TramTracker data service. Based on https://tramtracker.com.au/js/dataService.js."""

    def __init__(self: Self, session: ClientSession, *, calls: int = 1, period: float = 10) -> None:
        """Creates a new :class:`AsyncTramTrackerAPI` instance.

        :param session:           Calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` to be used as a context manager. If you wish to let the instance handle the session, use the alternative constructor method :meth:`create` instead
        :param calls:             Maximum number of calls that can be made to the service within the specified ``period``
        :param period:            Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :return:                  ``None``
        """

        self._limiter: Final[AsyncLimiter] = AsyncLimiter(calls, period)
        """HTTP requests rate limiter"""
        self._session: Final[ClientSession] = session
        """HTTP session used to make requests"""
        self._is_user_session: bool = True
        """Whether the session is user-supplied (and therefore whether to auto-close on instance deletion)"""

        _logger.info("AsyncTramTrackerAPI instance created")
        return

    @classmethod
    async def create(cls: Callable[..., Self], session: ClientSession | None = None, *, calls: int = 1, period: float = 10) -> Self:
        """Creates a new :class:`AsyncTramTrackerAPI` instance.

        :param session:           If specified, calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` to be used as a context manager (default is to create a new :class:`~aiohttp.ClientSession` instance to be used internally)
        :type session:            ~aiohttp.ClientSession | None
        :param calls:             Maximum number of calls that can be made to the service within the specified ``period``
        :param period:            Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :return:                  The new instance
        """

        if session is None:
            instance = cls(session=ClientSession(), calls=calls, period=period)
            instance._is_user_session = False
        else:
            instance = cls(session=session, calls=calls, period=period)

        return instance

    def __del__(self: Self) -> None:
        """Closes the underlying HTTP session if it wasn't supplied by the user and logs the prospective deletion of an instance into the module logger once there are no more references to it in the program.

        Note that Python does not guarantee that this will be called for any instance.

        :return: ``None``
        """

        if not self._is_user_session:
            self._session.close()
        _logger.info("AsyncTramTrackerAPI instance deleted")
        return

    async def call(self: Self, request: str) -> list[dict[str, str | int | float | bool | dict[str, str | int | list[str]] | None]] | dict[str, str | int | float | bool | None]:
        """Requests data from the TramTracker service and returns the response.

        :param request: The request, which is appended to the base URL of the service
        :return:        A :class:`list` or :class:`dict` of the response data, depending on the request
        """

        url = f"http://tramtracker.com.au/Controllers{request}"
        _logger.debug("Entering rate limiter context manager")
        async with self._limiter:  # Rate limit requests
            _logger.debug("Requesting from: " + url)
            r = await self._session.request("get", url)
        try:
            r.raise_for_status()
        except Exception:
            _logger.error("", exc_info=True)
            raise
        _logger.debug("Awaiting JSON decoder")
        result = await r.json()
        _logger.debug("Response: " + str(result))

        try:
            if ("HasError" in result and result["HasError"]) or ("hasError" in result and result["hasError"]):
                raise TramTrackerError(result["ResponseString"] if "ResponseString" in result else result["errorMessage"])
            assert ("ResponseObject" in result and result["ResponseObject"] is not None) or ("responseObject" in result and result["responseObject"] is not None)
        except Exception:
            _logger.error("", exc_info=True)
            raise

        return result["ResponseObject"] if "ResponseObject" in result else result["responseObject"]

    async def list_destinations(self: Self) -> list[TramDestination]:
        """Returns a list of termini for each primary tram route on the network.

        :return: A list detailing each route terminus
        """

        response = await self.call("/GetAllRoutes.ashx")
        return [TramDestination(route_id=element["InternalRouteNo"],
                                route_number=element["AlphaNumericRouteNo"] if element["AlphaNumericRouteNo"] is not None else str(element["RouteNo"]),
                                up_direction=element["IsUpDirection"],
                                destination=element["Destination"],
                                has_low_floor_trams=element["HasLowFloor"]
                                ) for element in response]

    async def list_stops(self: Self, route_id: int, up_direction: bool) -> list[TramStop]:
        """Returns a list of stops on the specified route and direction of travel.

        :param route_id:     The route identifier, as returned by :meth:`list_destinations()`
        :param up_direction: Set to ``True`` to get stops in the "up" direction or ``False`` to get stops in the "down" direction, as described by :meth:`list_destinations()`
        :return:             A list of stops on the route
        """

        response = await self.call(f"/GetStopsByRouteAndDirection.ashx?r={route_id}&u={"true" if up_direction else "false"}")
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

    async def get_stop(self: Self, stop_id: int) -> TramStop:
        """Returns information about the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return:        The stop details
        """

        response = await self.call(f"/GetStopInformation.ashx?s={stop_id}")
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

    async def list_routes_for_stop(self: Self, stop_id: int) -> list[str]:
        """Returns a list of route numbers for the primary routes that serve the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return:        A list of route numbers
        """

        response = await self.call(f"/GetPassingRoutes.ashx?s={stop_id}")
        return [element["RouteNo"] for element in response]

    async def next_trams(self: Self, stop_id: int, route_id: int | None = None, low_floor_tram: bool = False, as_of: datetime = datetime.now(tz=ZoneInfo("Australia/Melbourne"))) -> list[TramDeparture]:
        """Returns the details and times of the next trams to depart from the specified stop. The number of results returned can vary, but is usually three entries per destination.

        :param stop_id:        The TramTracker code of the stop
        :param route_id:       If specified, return next trams for the specified route identifier
        :param low_floor_tram: If set to ``True``, only departures with low-floor trams will be returned
        :param as_of:          The time from which to get departures; defaults to current system time
        :return:               A list of departures from the stop
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        as_of = as_of.astimezone(TZ_MELBOURNE)
        timestamp = round((as_of - EPOCH) / timedelta(milliseconds=1))
        response = await self.call(f"/GetNextPredictionsForStop.ashx?stopNo={stop_id}&routeNo={route_id if route_id is not None else 0}&isLowFloor={"true" if low_floor_tram else "false"}&ts={timestamp}")
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

    async def get_route_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the colour of the specified route as printed on public information paraphernalia.

        :param route_id: The route identifier
        :param as_of:    If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return:         A hexadecimal code representing the route colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = await self.call(f"/GetRouteColour.ashx?routeNo={route_id}&ts={timestamp}")
        return "#" + response["Colour"].lower()

    async def get_route_text_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the text font colour on public information paraphernalia if it was written on a background with the route's colour (e.g. the route iconography).

        :param route_id: The route identifier
        :param as_of:    If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return:         A hexadecimal code representing the text colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = await self.call(f"/GetRouteTextColour.ashx?routeNo={route_id}&ts={timestamp}")
        return "#" + response["Colour"].lower()
