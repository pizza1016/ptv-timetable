from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from ratelimit import limits, sleep_and_retry
from requests.models import Response
from requests.sessions import Session
from typing import cast, Final, Self
from zoneinfo import ZoneInfo
import logging
import platform
if platform.system() == "Windows":
    import tzdata

from .asyncapi import AsyncTramTrackerAPI
from .types import *
from . import _responsemodel

__all__ = ["TramTrackerAPI", "AsyncTramTrackerAPI"]

_logger: Final = logging.getLogger("ptv-timetable.tramtracker")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


class TramTrackerAPI(object):
    """Interface class for the TramTracker data service. Based on https://tramtracker.com.au/js/dataService.js."""

    def __init__[**_P, _R](self: Self, *, calls: int = 20, period: float = 60, ratelimit_handler: Callable[[Callable[_P, _R]], Callable[_P, _R]] = sleep_and_retry, session: Session | None = None) -> None:
        """Initialises a new :class:`TramTrackerAPI` instance.

        :param calls:             Maximum number of calls that can be made to the service within the specified ``period``
        :param period:            Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :param ratelimit_handler: Function decorator that handles :class:`~ratelimit.exception.RateLimitException` without re-raising it; defaults to :func:`~ratelimit.decorators.sleep_and_retry`. A custom handler should match the specified signature, otherwise the program's behaviour is undefined (there is no runtime checking of the suitability of the handler)
        :param session:           If specified, calls will be made using this HTTP session; this allows a :class:`~requests.sessions.Session` to be used as a context manager (default is to create a new :class:`~requests.sessions.Session` instance to be used internally)
        :return:                  ``None``

        .. versionchanged:: 0.2.1
            Added the ``calls``, ``period`` and ``ratelimit_handler`` parameters.

        .. versionchanged:: 0.4.0
            Renamed from ``TramTrackerService`` to ``TramTrackerAPI``. Added the ``session`` parameter.

        .. versionchanged:: 0.5.0
            Increased default rate limit from 1 call per 10 seconds to 20 calls per 60 seconds.
        """

        self._session = session if session is not None else Session()
        """HTTP session used to make requests"""
        self._is_user_session: Final[bool] = True if session is not None else False
        """Whether the session is user-supplied (and therefore whether to auto-close on instance deletion)"""

        self._get: Callable[..., Response] = ratelimit_handler(limits(calls, period)(self._session.get))
        """Session.get() method but rate-limited"""

        _logger.info("TramTrackerAPI instance created")
        return

    def __del__(self: Self) -> None:
        """Closes the underlying HTTP session if it wasn't supplied by the user and logs the prospective deletion of an instance into the module logger once there are no more references to it in the program.

        Note that Python does not guarantee that this will be called for any instance.

        :return: ``None``
        """

        if not self._is_user_session:
            self._session.close()
        _logger.info("TramTrackerAPI instance deleted")
        return

    def request(self: Self, path: str) -> _responsemodel.TramTrackerResponse:
        """Requests data from the TramTracker service and returns the response.

        :param path: The request, which is appended to the base URL of the service
        :return:     A :class:`list` or :class:`dict` of the response data, depending on the request

        .. versionchanged:: 0.5.0
            Renamed method from ``call``; now returns the whole server response including the enclosing object.
        """

        url = f"https://tramtracker.com.au/Controllers{path}"
        _logger.debug("Requesting from: " + url)
        r: Response = self._get(url)
        try:
            r.raise_for_status()
        except Exception:
            _logger.error("", exc_info=True)
            raise
        result: _responsemodel.TramTrackerResponse = r.json()
        _logger.debug("Response: " + str(result))

        try:
            if ("HasError" in result and result["HasError"]) or ("hasError" in result and result["hasError"]):
                raise TramTrackerError(result["ResponseString"] if "ResponseString" in result else result["errorMessage"])
            assert ("ResponseObject" in result and result["ResponseObject"] is not None) or ("responseObject" in result and result["responseObject"] is not None)
        except Exception:
            _logger.error("", exc_info=True)
            raise

        return result

    def list_destinations(self: Self) -> list[TramDestination]:
        """Returns a list of termini for each primary tram route on the network.

        :return: A list detailing each route terminus
        """

        response = cast(_responsemodel.DestinationsResponse, self.request("/GetAllRoutes.ashx"))
        return [TramDestination(route_id=element["InternalRouteNo"],
                                route_number=element["AlphaNumericRouteNo"] if element["AlphaNumericRouteNo"] is not None else str(element["RouteNo"]),
                                up_direction=element["IsUpDestination"],
                                destination=element["Destination"],
                                has_low_floor_trams=element["HasLowFloor"]
                                ) for element in response["ResponseObject"]]

    def list_stops(self: Self, route_id: int, up_direction: bool) -> list[TramStop]:
        """Returns a list of stops on the specified route and direction of travel.

        :param route_id:     The route identifier, as returned by :meth:`list_destinations()`
        :param up_direction: Set to ``True`` to get stops in the "up" direction or ``False`` to get stops in the "down" direction, as described by :meth:`list_destinations()`
        :return:             A list of stops on the route
        """

        response = cast(_responsemodel.StopsResponse, self.request(f"/GetStopsByRouteAndDirection.ashx?r={route_id}&u={"true" if up_direction else "false"}"))
        return [TramStop(stop_id=element["StopNo"],
                         stop_name=element["Description"],
                         stop_number=element["StopName"].split()[0],
                         locality=element["Suburb"],
                         location=(element["Latitude"], element["Longitude"]),
                         route_id=element["RouteNo"],
                         destination=element["Destination"],
                         distance_to_location=element["DistanceToLocation"],
                         city_direction=element["CityDirection"]
                         ) for element in response["ResponseObject"]]

    def get_stop(self: Self, stop_id: int) -> TramStop:
        """Returns information about the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return:        The stop details
        """

        response = cast(_responsemodel.StopResponse, self.request(f"/GetStopInformation.ashx?s={stop_id}"))
        element = response["ResponseObject"]
        return TramStop(stop_id=stop_id,
                        stop_name=element["StopName"],
                        stop_number=element["FlagStopNo"],
                        locality=element["Suburb"],
                        location=(element["Latitude"], element["Longitude"]),
                        route_id=element["RouteNo"],
                        destination=element["Destination"],
                        distance_to_location=element["DistanceToLocation"],
                        city_direction=element["CityDirection"]
                        )

    def list_routes_for_stop(self: Self, stop_id: int) -> list[str]:
        """Returns a list of route numbers for the primary routes that serve the specified stop.

        :param stop_id: The TramTracker code of the stop
        :return:        A list of route numbers
        """

        response = cast(_responsemodel.RoutesResponse, self.request(f"/GetPassingRoutes.ashx?s={stop_id}"))
        return [element["RouteNo"] for element in response["ResponseObject"]]

    def next_trams(self: Self, stop_id: int, route_id: int | None = None, low_floor_tram: bool = False, as_of: datetime = datetime.now(tz=ZoneInfo("Australia/Melbourne"))) -> list[TramDeparture]:
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
        response = cast(_responsemodel.DeparturesResponse, self.request(f"/GetNextPredictionsForStop.ashx?stopNo={stop_id}&routeNo={route_id if route_id is not None else 0}&isLowFloor={"true" if low_floor_tram else "false"}&ts={timestamp}"))
        return [TramDeparture(stop_id=stop_id,
                              trip_id=element["TripID"],
                              route_id=element["InternalRouteNo"],
                              route_number=element["HeadBoardRouteNo"],
                              primary_route_number=element["RouteNo"],
                              vehicle_id=element["VehicleNo"],
                              vehicle_class=element["TramClass"],
                              destination=element["Destination"],
                              tt_available=element["IsTTAvailable"],
                              low_floor_tram=element["IsLowFloorTram"],
                              air_conditioned=element["AirConditioned"],
                              display_ac_icon=element["DisplayAC"],
                              has_disruption=element["HasDisruption"],
                              disruptions=element["DisruptionMessage"]["Messages"],
                              has_special_event=element["HasSpecialEvent"],
                              special_event_message=element["SpecialEventMessage"],
                              has_planned_occupation=element["HasPlannedOccupation"],
                              planned_occupation_message=element["PlannedOccupationMessage"],
                              estimated_departure=(EPOCH + timedelta(milliseconds=int(TIMESTAMP_PATTERN.fullmatch(element["PredictedArrivalDateTime"]).group("timestamp")))).astimezone(TZ_MELBOURNE),
                              location=(element["Latitude"], element["Longitude"]),
                              occupancy_level=element["OccupancyLevel"],
                              AVM_timestamp=datetime.fromisoformat(element["AVMTimestamp"]).replace(tzinfo=TZ_MELBOURNE)
                              ) for element in response["responseObject"]]

    def get_route_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the colour of the specified route as printed on public information paraphernalia.

        :param route_id: The route identifier
        :param as_of:    If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return:         A hexadecimal code representing the route colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = cast(_responsemodel.ColourResponse, self.request(f"/GetRouteColour.ashx?routeNo={route_id}&ts={timestamp}"))
        return "#" + response["responseObject"]["Colour"].lower()

    def get_route_text_colour(self: Self, route_id: int, as_of: datetime = datetime.now(tz=TZ_MELBOURNE)) -> str:
        """Returns the RGB hexadecimal code for the text font colour on public information paraphernalia if it was written on a background with the route's colour (e.g. the route iconography).

        :param route_id: The route identifier
        :param as_of:    If specified, return the colour that was/will be used at the specified time; defaults to current system time
        :return:         A hexadecimal code representing the text colour
        """
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=TZ_MELBOURNE)
        timestamp = round((as_of - datetime(1970, 1, 1, tzinfo=timezone.utc)) / timedelta(milliseconds=1))
        response = cast(_responsemodel.ColourResponse, self.request(f"/GetRouteTextColour.ashx?routeNo={route_id}&ts={timestamp}"))
        return "#" + response["responseObject"]["Colour"].lower()
