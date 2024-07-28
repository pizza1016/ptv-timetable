from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from typing import cast, Final, Literal, overload, override, Self
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
import urllib.parse
if platform.system() == "Windows":
    import tzdata

__all__ = ["TimetableAPI", "METROPOLITAN_TRAIN", "METRO_TRAIN", "MET_TRAIN", "METRO", "TRAM", "BUS", "REGIONAL_TRAIN", "REG_TRAIN", "COACH", "VLINE", "EXPAND_ALL", "EXPAND_STOP", "EXPAND_ROUTE", "EXPAND_RUN", "EXPAND_DIRECTION", "EXPAND_DISRUPTION", "EXPAND_VEHICLE_DESCRIPTOR", "EXPAND_VEHICLE_POSITION", "EXPAND_NONE"]

type _Values = str | int | float | bool | datetime | _Record
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

type ExpandType = Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]
type RouteType = Literal[0, 1, 2, 3]

TZ_MELBOURNE = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""
UUID_PATTERN = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")
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

_logger = logging.getLogger("ptv-timetable.ptv_timetable")
"""Logger for this module"""
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.NullHandler())


@dataclass(kw_only=True)
class TimetableData(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        """
        Constructs a new instance of this ``PTVData`` subclass by converting the specified API response data.

        :param kwargs: A dictionary unpacking with the data to instantiate
        :return: The newly constructed instance
        """
        ...


@dataclass(kw_only=True, slots=True)
class PathGeometry(TimetableData):
    """Represents the physical geometry of the attached route or run."""

    direction_id: int
    """Identifier of the direction of travel represented by this geometry"""
    valid_from: str
    """Date geometry is valid from"""
    valid_to: str
    """Date geometry is valid to"""
    paths: list[str]
    """Strings of coordinate pairs that draws the path"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        return cls(**kwargs)


@dataclass(kw_only=True, slots=True)
class StopTicket(TimetableData):
    """Ticketing information for the attached stop."""

    ticket_type: Literal["myki", "paper", "both", ""]
    """Appears to be deprecated/unused (always returns empty string). Whether this stop uses myki ticketing, paper ticketing, or both"""
    zone: str
    """Description of the ticketing zone"""
    is_free_fare_zone: bool
    """Whether this stop is in a free fare zone"""
    ticket_machine: bool
    """Whether this stop has ticket machines"""
    ticket_checks: bool
    """Meaning is unclear"""
    vline_reservation: bool
    """Whether a V/Line reservation is required to travel to or from this station or stop; value should not be used for modes other than V/Line"""
    ticket_zones: list[int]
    """Ticketing zone(s) this stop is in"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        return cls(**kwargs)


@dataclass(kw_only=True, slots=True)
class StopContact(TimetableData):
    """Operator contact details for the attached stop."""

    phone: str | None
    """Main phone number of stop"""
    lost_property: str | None
    """Phone number for lost property"""
    feedback: str | None
    """Phone number to provide feedback"""
    lost_property_contact_number: None
    """Appears to be deprecated/unused (always returns None)"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        return cls(**kwargs)


@dataclass(kw_only=True, slots=True)
class StopLocation(TimetableData):
    """Location details for the attached stop."""

    postcode: int
    """Postcode of stop"""
    municipality: str
    """Municipality (local government area) of location"""
    municipality_id: int
    """Municipality identifier"""
    locality: str
    """Locality (suburb/town) of this stop"""
    primary_stop_name: str
    """Name of one of the roads near this stop (usually the crossing road, or "at" road), or a nearby landmark"""
    road_type_primary: str
    """Road name suffix for 'primary_stop_name'"""
    second_stop_name: str
    """Name of one of the roads near this stop (usually the road of travel, or "on" road); may be empty"""
    road_type_second: str
    """Road name suffix for 'second_stop_name'"""
    bay_number: int
    """For bus interchanges, the bay number of the particular stop"""
    latitude: float
    """Latitude coordinate of this stop's location"""
    longitude: float
    """Longitude coordinate of this stop's location"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        bay_number = kwargs.pop("bay_nbr")
        locality = kwargs.pop("suburb")
        gps = kwargs.pop("gps")
        latitude = gps["latitude"]
        longitude = gps["longitude"]
        return cls(bay_number=bay_number, locality=locality, latitude=latitude, longitude=longitude, **kwargs)


@dataclass(kw_only=True, slots=True)
class StopAmenities(TimetableData):
    """Amenities at the attached stop."""

    seat_type: Literal["", "Shelter"]
    """Type of seating; empty string if none"""
    pay_phone: bool
    """Whether there is a public telephone at this stop"""
    indoor_waiting_area: bool
    """Whether there is an indoor waiting lounge at this stop"""
    sheltered_waiting_area: bool
    """Whether there is a sheltered waiting area at this stop"""
    bicycle_rack: int
    """Number of public bicycle racks at this stop"""
    bicycle_cage: bool
    """Whether there is a secure bicycle cage at this stop"""
    bicycle_locker: int
    """Number of bicycle lockers at this stop"""
    luggage_locker: int
    """Number of luggage lockers at this stop"""
    kiosk: bool
    """Meaning unclear"""
    seat: str
    """Appears to be deprecated/unused (always returns empty string)"""
    stairs: str
    """Appears to be deprecated/unused (always returns empty string)"""
    baby_change_facility: str
    """Appears to be deprecated/unused (always returns empty string)"""
    parkiteer: None
    """Appears to be deprecated/unused (always returns None). Whether there is a Parkiteer (Bicycle Network) bicycle storage facility at this stop; None if not applicable or information unavailable"""
    replacement_bus_stop_location: str
    """Appears to be deprecated/unused (always returns empty string). Location of the replacement bus stop"""
    QTEM: None
    """Appears to be deprecated/unused (always returns None)"""
    bike_storage: None
    """Appears to be deprecated/unused (always returns None)"""
    PID: bool
    """Whether there are passenger information displays at this stop"""
    ATM: None
    """Whether there is an automated teller machine at this stop"""
    travellers_aid: bool | None
    """Whether Traveller's Aid facilities are available at this stop; None if not applicable"""
    premium_stop: None
    """Appears to be deprecated/unused (always returns None)"""
    PSOs: None
    """Appears to be deprecated/unused (always returns None). Whether Protective Services Officers patrol this stop; None if not applicable"""
    melb_bike_share: None
    """Defunct (scheme no longer exists). Whether there are Melbourne Bike Share bicycle rentals available at this stop; None if not applicable or information unavailable"""
    luggage_storage: None
    """Appears to be deprecated/unused (always returns empty string). Whether luggage storage services are available at this stop; None if not applicable or information unavailable"""
    luggage_check_in: None
    """Appears to be deprecated/unused (always returns empty string). Whether luggage check-in facilities are available at this stop; None if not applicable or information unavailable"""
    toilet: bool
    """Whether there is a public toilet at or near this stop"""
    taxi_rank: bool
    """Whether there is a taxi rank at or near this stop"""
    car_parking: int | None
    """Number of fee-free parking spaces at this stop; None if not applicable"""
    cctv: bool
    """Whether there are closed-circuit television cameras at this stop"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        replacement_bus_stop_location = kwargs.pop("replacement_bus_stop_loc")
        if kwargs["car_parking"] == "":
            car_parking = None
            kwargs.pop("car_parking")
        else:
            car_parking = int(kwargs.pop("car_parking"))
        return cls(replacement_bus_stop_location=replacement_bus_stop_location, car_parking=car_parking, **kwargs)


@dataclass(kw_only=True, slots=True)
class Wheelchair(TimetableData):
    """Wheelchair accessibility information for the attached stop."""

    accessible_ramp: bool
    """Whether there is ramp access to this stop or its platforms"""
    parking: bool | None
    """Whether there is DDA-compliant parking at this stop; None if not applicable"""
    telephone: bool | None
    """Whether there is a DDA-compliant telephone at this stop; None if not applicable"""
    toilet: bool | None
    """Whether there is a DDA-compliant toilet at this stop; None if not applicable"""
    low_ticket_counter: bool | None
    """Whether there is a DDA-compliant low ticket counter at this stop; None if not applicable"""
    manoeuvring: bool | None
    """Whether there is enough space for mobility devices to board or alight a public transport vehicle; None if not applicable or information unavailable"""
    raised_platform: bool | None
    """Whether the platform at this stop is raised to the height of the vehicle's floor; None if not applicable or information unavailable"""
    raised_platform_shelter: bool | None
    """Whether there is shelter near the raised platform; None if not applicable or information unavailable"""
    ramp: bool | None
    """Whether there are ramps with a height to length ratio less than 1:14 at this stop; None if not applicable or information unavailable"""
    secondary_path: bool | None
    """Whether there is a path outside this stop perimeter or boundary connecting to this stop that is accessible; None if not applicable or information unavailable"""
    steep_ramp: bool | None
    """Whether there are ramps with a height to length ratio greater than 1:14 at this stop; None if not applicable or information unavailable"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        manoeuvring = kwargs.pop("manouvering")
        raised_platform_shelter = kwargs.pop("raised_platform_shelther")
        return cls(manoeuvring=manoeuvring, raised_platform_shelter=raised_platform_shelter, **kwargs)


@dataclass(kw_only=True, slots=True)
class StopAccessibility(TimetableData):
    """Accessibility information for the attached stop."""

    platform_number: int | None
    """The platform number of the stop that the data in this instance applies to; 0 if it applies to the entire stop in general; None if not applicable"""
    lighting: bool
    """Whether there is lighting at this stop"""
    audio_customer_information: bool | None
    """Whether there is at least one facility that provides audio passenger information at this stop; None if not applicable"""
    escalator: bool | None
    """Whether there is at least one escalator that complies with the Disability Discrimination Act 1992 (Cth); None if not applicable"""
    hearing_loop: bool | None
    """Whether hearing loops are available at this stop; None if not applicable"""
    lift: bool | None
    """Whether there are lifts at this stop; None if not applicable"""
    stairs: bool | None
    """Whether there are stairs at this stop; None if not applicable"""
    stop_accessible: bool | None
    """Whether this stop is "accessible"; None if not applicable"""
    tactile_ground_surface_indicator: bool
    """Whether there are tactile guide tiles or paving at this stop"""
    waiting_room: bool | None
    """Whether there is a designated waiting lounge at this stop; None if not applicable"""
    wheelchair: Wheelchair
    """Wheelchair accessibility information for this stop"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        wheelchair = kwargs.pop("wheelchair")
        return cls(wheelchair=Wheelchair.load(**wheelchair), **kwargs)


@dataclass(kw_only=True, slots=True)
class StopStaffing(TimetableData):
    """Staffing hours for the attached stop"""

    mon_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Monday morning staffing hours start time"""
    mon_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Monday morning staffing hours end time"""
    mon_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Monday evening staffing hours start time"""
    mon_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Monday evening staffing hours end time"""
    tue_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Tuesday morning staffing hours start time"""
    tue_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Tuesday morning staffing hours end time"""
    tue_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Tuesday evening staffing hours start time"""
    tue_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Tuesday evening staffing hours end time"""
    wed_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Wednesday morning staffing hours start time"""
    wed_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Wednesday morning staffing hours end time"""
    wed_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Wednesday evening staffing hours start time"""
    wed_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Wednesday evening staffing hours end time"""
    thu_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Thursday morning staffing hours start time"""
    thu_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Thursday morning staffing hours end time"""
    thu_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Thursday evening staffing hours start time"""
    thu_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Thursday evening staffing hours end time"""
    fri_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Friday morning staffing hours start time"""
    fri_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Friday morning staffing hours end time"""
    fri_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Friday evening staffing hours start time"""
    fri_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Friday evening staffing hours end time"""
    sat_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Saturday morning staffing hours start time"""
    sat_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Saturday morning staffing hours end time"""
    sat_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Saturday evening staffing hours start time"""
    sat_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Saturday evening staffing hours end time"""
    sun_am_from: str
    """Appears to be deprecated/unused (always returns empty string). Sunday morning staffing hours start time"""
    sun_am_to: str
    """Appears to be deprecated/unused (always returns empty string). Sunday morning staffing hours end time"""
    sun_pm_from: str
    """Appears to be deprecated/unused (always returns empty string). Sunday evening staffing hours start time"""
    sun_pm_to: str
    """Appears to be deprecated/unused (always returns empty string). Sunday evening staffing hours end time"""
    ph_from: str
    """Appears to be deprecated/unused (always returns empty string). Public holiday staffing hours start time"""
    ph_to: str
    """Appears to be deprecated/unused (always returns empty string). Public holiday staffing hours end time"""
    ph_additional_text: str
    """Appears to be deprecated/unused (always returns empty string). Additional details about staffing on public holidays"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        wed_pm_to = kwargs.pop("wed_pm_To")
        return cls(wed_pm_to=wed_pm_to, **kwargs)


@dataclass(kw_only=True, slots=True)
class Route(TimetableData):
    """Represents a route on the network."""

    route_id: int
    """Identifier of this route"""
    route_type: int
    """Identifier of the travel mode of this route"""
    route_name: str
    """Name of this route"""
    route_number: str
    """Public-facing route number of this route"""
    route_gtfs_id: str
    """Identifier for this route in the General Transit Feed Specification"""
    geometry: list[PathGeometry] | None = None
    """Physical geometry of this route"""
    route_service_status: dict[Literal["description", "timestamp"], str | datetime] | None = None
    """Service status of the route; None if API did not provide this information"""

    # From /v3/disruptions/...
    route_direction_id: int | None = None
    """For a disruption, combined identifier for the route and travel direction affected by the disruption; None if not applicable"""
    direction_id: int | None = None
    """For a disruption, identifier of travel direction affected by the disruption; None if not applicable"""
    direction_name: str | None = None
    """For a disruption, destination of travel direction affected by the disruption; None if not applicable"""
    service_time: str | None = None
    """For a disruption, time of the run/service affected by the disruption; None if not applicable, or disruption affects multiple or no runs/services"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        route_name = kwargs.pop("route_name").strip()
        geometry = kwargs.pop("geopath") if "geopath" in kwargs else None
        if geometry is not None:
            geometry = [PathGeometry(**item) for item in geometry]
        route_service_status = kwargs.pop("route_service_status") if "route_service_status" in kwargs else None
        if route_service_status is not None:
            route_service_status["timestamp"] = datetime.fromisoformat(route_service_status["timestamp"]).astimezone(TZ_MELBOURNE)
        direction = kwargs.pop("direction") if "direction" in kwargs else None
        route_direction_id = direction["route_direction_id"] if direction is not None else None
        direction_id = direction["direction_id"] if direction is not None else None
        direction_name = direction["direction_name"] if direction is not None else None
        service_time = direction["service_time"] if direction is not None else None
        return cls(route_name=route_name, geometry=geometry, route_service_status=route_service_status, route_direction_id=route_direction_id, direction_id=direction_id, direction_name=direction_name, service_time=service_time, **kwargs)


@dataclass(kw_only=True, slots=True)
class Stop(TimetableData):
    """Represents a particular transport stop."""

    stop_id: int
    """Identifier of this stop"""
    route_type: int | None = None
    """Identifier of the travel mode of this stop; None if this was created by 'Disruptions'"""
    stop_name: str
    """Name of this stop"""
    locality: str | None = None
    """Locality (suburb/town) this stop is in; None if the API response did not return this information"""
    stop_latitude: float | None = None
    """Latitude coordinate of the stop's location; None if the API response did not return this information"""
    stop_longitude: float | None = None
    """Longitude coordinate of the stop's location; None if the API response did not return this information"""
    stop_distance: float | None = None
    """If a location was specified in the API call, distance in metres between this stop and that location; otherwise, 0.0 or None"""
    stop_landmark: str | None = None
    """Notable landmarks near this stop; "" (empty string) if none; None if this was created by 'Disruptions'"""
    stop_sequence: int | None = None
    """Sort key for this stop along a route or run that is the subject of the API call; if neither were provided, value is 0"""
    stop_ticket: StopTicket | None = None
    """Ticketing information for this stop; None if the API response did not return this information"""

    # From /v3/stops/...
    point_id: int | None = None
    """Identifier of this stop in the PTV static timetable dump; None if the API operation doesn't use this field"""
    disruption_ids: list[int] | None = None
    """Current or future disruptions affecting this stop; None if the API operation doesn't use this field"""
    routes: list[Route] | None = None
    """List of routes serving this stop; None if the API operation doesn't use this field"""
    operating_hours: str | None = None
    """Description of railway station opening hours; None if the API operation doesn't use this field"""
    mode_id: int | None = None
    """Purpose unclear; appears to correspond to disruption modes, which is not currently implemented in this module as it duplicates the purpose of RouteType"""
    station_details_id: int | None = None
    """Appears to be deprecated/unused (always returns 0)"""
    flexible_stop_opening_hours: str | None = None
    """Appears to be deprecated/unused (always returns empty string)"""
    stop_contact: StopContact | None = None
    """Operator contact information for this stop; None if not requested from API"""
    stop_location: StopLocation | None = None
    """Location information about this stop; None if not requested from API"""
    stop_amenities: StopAmenities | None = None
    """Facilities available at this stop; None if not requested from API"""
    stop_accessibility: StopAccessibility | None = None
    """Information about accessibility features available at this stop; None if not requested from API"""
    stop_staffing: StopStaffing | None = None
    """Staffing information for this stop; None if not requested from API"""
    station_type: Literal["Premium Station", "Host Station", "Unstaffed Station"] | None = None
    """Type of metropolitan train station: a premium station is staffed from first to last train and a host station is staffed only in the morning peak; None for other modes or if the API operation doesn't use this field"""
    station_description: str | None = None
    """Additional information about this stop"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        stop_name = kwargs.pop("stop_name").strip()
        locality = kwargs.pop("stop_suburb") if "stop_suburb" in kwargs else None
        stop_ticket = StopTicket.load(**kwargs.pop("stop_ticket")) if "stop_ticket" in kwargs and kwargs["stop_ticket"] is not None else kwargs.pop("stop_ticket", None)
        routes = [Route.load(**item) for item in kwargs.pop("routes")] if "routes" in kwargs and kwargs["routes"] is not None else kwargs.pop("routes", None)
        stop_contact = StopContact.load(**kwargs.pop("stop_contact")) if "stop_contact" in kwargs and kwargs["stop_contact"] is not None else kwargs.pop("stop_contact", None)
        stop_location = StopLocation.load(**kwargs.pop("stop_location")) if "stop_location" in kwargs and kwargs["stop_location"] is not None else kwargs.pop("stop_location", None)
        stop_amenities = StopAmenities.load(**kwargs.pop("stop_amenities")) if "stop_amenities" in kwargs and kwargs["stop_amenities"] is not None else kwargs.pop("stop_amenities", None)
        stop_accessibility = StopAccessibility.load(**kwargs.pop("stop_accessibility")) if "stop_accessibility" in kwargs and kwargs["stop_accessibility"] is not None else kwargs.pop("stop_accessibility", None)
        stop_staffing = StopStaffing.load(**kwargs.pop("stop_staffing")) if "stop_staffing" in kwargs and kwargs["stop_staffing"] is not None else kwargs.pop("stop_staffing", None)
        return cls(stop_name=stop_name, locality=locality, stop_ticket=stop_ticket, routes=routes, stop_contact=stop_contact, stop_location=stop_location, stop_amenities=stop_amenities, stop_accessibility=stop_accessibility, stop_staffing=stop_staffing, **kwargs)


@dataclass(kw_only=True, slots=True)
class Departure(TimetableData):
    """Represents a specific departure from a specific stop."""

    stop_id: int
    """Identifier of departing stop"""
    route_id: int
    """Identifier of route of service"""
    direction_id: int
    """Travel direction identifier"""
    run_ref: str
    """Run/service identifier"""
    disruption_ids: list[int]
    """List of identifiers of disruptions affecting this stop and/or service"""
    scheduled_departure: datetime
    """Departure time of service as timetabled"""
    estimated_departure: datetime | None
    """Estimated real-time departure time; None if real-time departure time is unavailable"""
    at_platform: bool
    """Whether the train servicing this run is stopped at the platform"""
    platform_number: str
    """Expected platform number the train will depart from; this may change at any time up to prior to arriving at the stop"""
    flags: str
    """TODO"""
    departure_sequence: int
    """Sort key for this stop in a sequence of stops for this run"""

    # From /v3/pattern/...
    skipped_stops: list[Stop] | None = None
    """After departing from this stop, a sequence of stops that are skipped prior to arriving at the next departure point"""

    # Undocumented
    departure_note: str | None
    """Notes about this departure (appears to be used to indicate whether a metropolitan train service runs via the City Loop or not)"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        scheduled_departure = datetime.fromisoformat(kwargs.pop("scheduled_departure_utc")).astimezone(TZ_MELBOURNE)
        estimated_departure = datetime.fromisoformat(kwargs.pop("estimated_departure_utc")).astimezone(TZ_MELBOURNE) if kwargs["estimated_departure_utc"] is not None else kwargs.pop("estimated_departure_utc")
        skipped_stops = [Stop(**item) for item in kwargs.pop("skipped_stops")] if "skipped_stops" in kwargs and kwargs["skipped_stops"] is not None else kwargs.pop("skipped_stops", None)
        kwargs.pop("run_id")
        return cls(scheduled_departure=scheduled_departure, estimated_departure=estimated_departure, skipped_stops=skipped_stops, **kwargs)


@dataclass(kw_only=True, slots=True)
class VehiclePosition(TimetableData):
    """Represents the position of the attached vehicle."""

    latitude: float | None
    """Latitude coordinate of the vehicle's position; None if this information is unavailable"""
    longitude: float | None
    """Longitude coordinate of the vehicle's position; None if this information is unavailable"""
    easting: float | None
    """Easting of the vehicle's position in the easting-northing system; None if this information is unavailable"""
    northing: float | None
    """Northing of the vehicle's position easting-northing system; None if this information is unavailable"""
    direction: str
    """Description of the direction of travel (e.g. "inbound", "outbound")"""
    bearing: float | None
    """Vehicle's current direction of travel in degrees clockwise from geographic north; None if this information is unavailable"""
    supplier: str
    """Source of vehicle information"""
    as_of: datetime | None
    """Date and time at which this position information is current"""
    expires: datetime | None
    """Date and time at which this position information is no longer valid"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        as_of = datetime.fromisoformat(kwargs.pop("datetime_utc")).astimezone(TZ_MELBOURNE) if kwargs["datetime_utc"] is not None else kwargs.pop("datetime_utc")
        expires = datetime.fromisoformat(kwargs.pop("expiry_time")).astimezone(TZ_MELBOURNE) if kwargs["expiry_time"] is not None else kwargs.pop("expiry_time")
        return cls(as_of=as_of, expires=expires, **kwargs)


@dataclass(kw_only=True, slots=True)
class VehicleDescriptor(TimetableData):
    """Describes information about a vehicle on a run."""

    operator: str | None
    """Transport operator responsible for the vehicle; None or "" (empty string) if this information is unavailable"""
    id: str | None
    """Vehicle identifier used by the operator; None if this information is unavailable"""
    low_floor: bool | None
    """Whether the vehicle allows for step-free access at designated stops; None if this information is unavailable"""
    air_conditioned: bool | None
    """Whether the vehicle is air-conditioned; None if this information is unavailable"""
    description: str | None
    """Description of the vehicle make/model and configuration; None if this information is unavailable"""
    supplier: str | None
    """Source of vehicle information"""
    length: str | None
    """Length of the vehicle; None if this information is unavailable"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        return cls(**kwargs)


@dataclass(kw_only=True, slots=True)
class Run(TimetableData):
    """Represents a particular run or service along a route."""

    run_ref: str
    """Identifier of this run"""
    route_id: int
    """Identifier of the route this run belongs to"""
    route_type: int
    """Identifier of the travel mode of this run"""
    final_stop_id: int
    """Identifier of the terminating stop of this run"""
    destination_name: str | None
    """Public-facing destination name of this run; sometimes returns None (unclear why)"""
    status: Literal["scheduled", "updated"]
    """Status of this metropolitan train service; "scheduled" for all other modes"""
    direction_id: int
    """Identifier of the direction of travel of this run"""
    run_sequence: int
    """Sort key for this run in a chronological list of runs for this route and direction of travel"""
    express_stop_count: int
    """Number of skipped stops in this run"""
    vehicle_position: VehiclePosition | None
    """Real-time vehicle position information where available; None if this information was not requested from the API"""
    vehicle_descriptor: VehicleDescriptor | None
    """Information on the vehicle operating this service, where available; None if this information was not requested from the API"""
    geometry: list[PathGeometry]
    """Physical geometry of this run's journey; [] (empty list) if not requested from API"""
    interchange: dict | None
    """Indicates, if any, the run this service will operate after terminating; None if this information was not requested from the API"""

    # Undocumented
    run_note: str | None
    """Notes about this run"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        kwargs.pop("run_id")
        destination_name = kwargs.pop("destination_name")
        if destination_name is not None:
            destination_name = destination_name.strip()
        geometry = [PathGeometry.load(**item) for item in kwargs.pop("geopath")]
        vehicle_position = VehiclePosition.load(**kwargs.pop("vehicle_position")) if kwargs["vehicle_position"] is not None else kwargs.pop("vehicle_position")
        vehicle_descriptor = VehicleDescriptor.load(**kwargs.pop("vehicle_descriptor")) if kwargs["vehicle_descriptor"] is not None else kwargs.pop("vehicle_descriptor")
        return cls(destination_name=destination_name, geometry=geometry, vehicle_position=vehicle_position, vehicle_descriptor=vehicle_descriptor, **kwargs)


@dataclass(kw_only=True, slots=True)
class Direction(TimetableData):
    """Represents a direction of travel on a particular route."""

    direction_id: int
    """Identifier for direction of travel"""
    direction_name: str
    """Name of direction of travel"""
    route_direction_description: str | None = None
    """Detailed description of this direction of travel along this route, as publicly displayed on the PTV website; not returned by the Departures API"""
    route_id: int
    """Identifier for the route specified by this direction of travel"""
    route_type: int
    """Identifier for the mode of travel of this route and destination"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        return cls(**kwargs)


@dataclass(kw_only=True, slots=True)
class Disruption(TimetableData):
    """Represents a service disruption."""

    disruption_id: int
    """Disruption identifier"""
    title: str
    """Disruption title"""
    url: str
    """URL to get more information"""
    description: str
    """Summary of the disruption"""
    disruption_status: Literal["Planned", "Current"]
    """Status of the disruption"""
    disruption_type: Literal["Planned Works", "Planned Closure", "Service Information", "Minor Delays", "Major Delays", "Part Suspended"]
    """Type of disruption"""
    published_on: datetime
    """Date and time this disruption was published"""
    last_updated: datetime
    """Date and time information about this disruption was last updated"""
    from_date: datetime
    """Date and time this disruption began/will begin"""
    to_date: datetime | None
    """Date and time this disruption will end; None if unknown or uncertain"""
    routes: list[Route]
    """Routes affected by this disruption"""
    stops: list[Stop]
    """Stops affected by this disruption"""
    colour: str
    """Hex code for the alert colour on the disruption website"""
    display_on_board: bool
    """Indicates if this disruption is displayed on the PTV disruption boards across the network"""
    display_status: bool
    """Indicates if this disruption updates the service status of the affected routes on the disruption boards (presumably)"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        published_on = datetime.fromisoformat(kwargs.pop("published_on")).astimezone(TZ_MELBOURNE)
        last_updated = datetime.fromisoformat(kwargs.pop("last_updated")).astimezone(TZ_MELBOURNE)
        from_date = datetime.fromisoformat(kwargs.pop("from_date")).astimezone(TZ_MELBOURNE)
        to_date = datetime.fromisoformat(kwargs.pop("to_date")).astimezone(TZ_MELBOURNE) if kwargs["to_date"] is not None else kwargs.pop("to_date")
        routes = [Route.load(**item) for item in kwargs.pop("routes")]
        stops = [Stop.load(**item) for item in kwargs.pop("stops")]
        return cls(published_on=published_on, last_updated=last_updated, from_date=from_date, to_date=to_date, routes=routes, stops=stops, **kwargs)


@dataclass(kw_only=True, slots=True)
class StoppingPattern(TimetableData):
    """Represents a stopping pattern for a particular run. Sequence specified in departures field."""

    disruptions: list[Disruption]
    """List of disruptions affecting this run or the relevant routes and stops"""
    departures: list[Departure]
    """Sequence of departures from stops made by this run"""
    stops: dict[int, Stop]
    """Mapping of the relevant stop identifiers to Stop objects"""
    routes: dict[int, Route]
    """Mapping of the relevant route identifiers to Route objects"""
    runs: dict[str, Run]
    """Mapping of the relevant run identifiers to Run objects"""
    directions: dict[int, Direction]
    """Mapping of the relevant travel direction identifiers to Direction objects"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        disruptions = [Disruption.load(**item) for item in kwargs.pop("disruptions")]
        departures = [Departure.load(**item) for item in kwargs.pop("departures")]
        stops = {int(key): Stop.load(**value) for key, value in kwargs.pop("stops").items()}
        routes = {int(key): Route.load(**value) for key, value in kwargs.pop("routes").items()}
        runs = {key: Run.load(**value) for key, value in kwargs.pop("runs").items()}
        directions = {int(key): Direction.load(**value) for key, value in kwargs.pop("directions").items()}
        return cls(disruptions=disruptions, departures=departures, stops=stops, routes=routes, runs=runs, directions=directions)


@dataclass(kw_only=True, slots=True)
class DeparturesResponse(TimetableData):
    """Response from the departures API request; also contains any relevant route, service and stop details."""

    departures: list[Departure]
    """Departures returned from the API request"""
    stops: dict[int, Stop]
    """Mapping of stop identifiers to stop objects related to the returned departures"""
    routes: dict[int, Route]
    """Mapping of route identifiers to route objects related to the returned departures"""
    runs: dict[str, Run]
    """Mapping of run identifiers to run objects related to the returned departures"""
    directions: dict[int, Direction]
    """Mapping of direction identifiers to direction objects related to the returned departures"""
    disruptions: dict[int, Disruption]
    """Mapping of disruption identifiers to disruption objects related to the returned departures"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        departures = [Departure.load(**item) for item in kwargs.pop("departures")]
        stops = {int(key): Stop.load(**value) for key, value in kwargs.pop("stops").items()}
        routes = {int(key): Route.load(**value) for key, value in kwargs.pop("routes").items()}
        runs = {key: Run.load(**value) for key, value in kwargs.pop("runs").items()}
        directions = {int(key): Direction.load(**value) for key, value in kwargs.pop("directions").items()}
        disruptions = {int(key): Disruption.load(**value) for key, value in kwargs.pop("disruptions").items()}
        kwargs.pop("status")
        return cls(departures=departures, stops=stops, routes=routes, runs=runs, directions=directions, disruptions=disruptions)


@dataclass(kw_only=True, slots=True)
class Outlet(TimetableData):
    """Represents a ticket outlet."""

    outlet_slid_spid: str
    """Outlet SLID/SPID (beats me as to what that means, but it's some sort of identifier); PTV hubs return an empty string"""
    outlet_business: str
    """Name of the business"""
    outlet_latitude: float
    """Latitude coordinate of the outlet's position"""
    outlet_longitude: float
    """Longitude coordinate of the outlet's position"""
    street_address: str
    """Street address of the outlet"""
    locality: str
    """Locality/suburb/town of the outlet"""
    outlet_postcode: int
    """Postcode of the outlet"""
    outlet_business_hour_mon: str | None
    """Outlet's business hours on Mondays"""
    outlet_business_hour_tue: str | None
    """Outlet's business hours on Tuesdays"""
    outlet_business_hour_wed: str | None
    """Outlet's business hours on Wednesdays"""
    outlet_business_hour_thu: str | None
    """Outlet's business hours on Thursdays"""
    outlet_business_hour_fri: str | None
    """Outlet's business hours on Fridays"""
    outlet_business_hour_sat: str | None
    """Outlet's business hours on Saturdays"""
    outlet_business_hour_sun: str | None
    """Outlet's business hours on Sundays"""
    outlet_notes: str | None
    """Additional notes about the ticket outlet"""
    outlet_distance: float | None = None
    """Distance of the outlet from the search location (for API search operations); 0 if no location is provided, None if the operation doesn't use this field"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        street_address = kwargs.pop("outlet_name")
        locality = kwargs.pop("outlet_suburb")
        outlet_business_hour_thu = kwargs.pop("outlet_business_hour_thur")
        return cls(street_address=street_address, locality=locality, outlet_business_hour_thu=outlet_business_hour_thu, **kwargs)


@dataclass(kw_only=True, slots=True)
class FareEstimate(TimetableData):
    """Fare estimate for the specified travel. All fares in AUD."""

    early_bird_travel: bool
    """Whether the touch on and off are made at metropolitan train stations on a non-public-holiday weekday before 7:15 am Melbourne time"""
    free_fare_zone: bool
    """Whether this journey is entirely within a free fare zone"""
    weekend: bool
    """Whether this journey is made on a weekend or public holiday"""
    zones: list[int]
    """List of fare zones this fare estimate is valid for"""

    full_2_hour_peak: float
    """
    Standard fare for 2 hours of travel at any time of day.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    full_2_hour_off_peak: float
    """
    Standard fare for 2 hours of travel if tap on occurs outside designated peak periods.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    full_weekday_cap_peak: float
    """Standard daily cap for travel across the network at any time of day on weekdays"""
    full_weekday_cap_off_peak: float
    """Standard daily cap for travel across the network on weekdays if tap on occurs entirely outside designated peak periods"""
    full_weekend_cap: float
    """Standard daily cap for travel across the network on weekends"""
    full_holiday_cap: float
    """Standard daily cap for travel across the network on statutory public holidays"""
    full_pass_7_days_total: float
    """Standard fare for unlimited travel for one week (total cost)"""
    full_pass_28_to_69_days: float
    """Standard fare, per day, for unlimited travel for 28 to 69 days"""
    full_pass_70_plus_days: float
    """Standard fare, per day, for unlimited travel for 70 to 325 days; passes for 326 to 365 days cost the same total amount as a 325-day pass"""
    concession_2_hour_peak: float
    """
    Concession fare for 2 hours of travel at any time of day.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    concession_2_hour_off_peak: float
    """
    Concession fare for 2 hours of travel if tap on occurs outside designated peak periods.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    concession_weekday_cap_peak: float
    """Concession daily cap for travel across the network at any time of day on weekdays"""
    concession_weekday_cap_off_peak: float
    """Concession daily cap for travel across the network on weekdays if tap on occurs entirely outside designated peak periods"""
    concession_weekend_cap: float
    """Concession daily cap for travel across the network on weekends"""
    concession_holiday_cap: float
    """Concession daily cap for travel across the network on statutory public holidays"""
    concession_pass_7_days_total: float
    """Concession fare for unlimited travel for one week (total cost)"""
    concession_pass_28_to_69_days: float
    """Concession fare, per day, for unlimited travel for 28 to 69 days"""
    concession_pass_70_plus_days: float
    """Concession fare, per day, for unlimited travel for 70 to 325 days; passes for 326 to 365 days cost the same total amount as a 325-day pass"""
    senior_2_hour_peak: float
    """
    Senior fare for 2 hours of travel at any time of day.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    senior_2_hour_off_peak: float
    """
    Senior fare for 2 hours of travel if tap on occurs outside designated peak periods.
    
    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.
    
    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    senior_weekday_cap_peak: float
    """Senior daily cap for travel across the network at any time of day on weekdays"""
    senior_weekday_cap_off_peak: float
    """Senior daily cap for travel across the network on weekdays if tap on occurs entirely outside designated peak periods"""
    senior_weekend_cap: float
    """Senior daily cap for travel across the network on weekends"""
    senior_holiday_cap: float
    """Senior daily cap for travel across the network on statutory public holidays"""
    senior_pass_7_days_total: float
    """Senior fare for unlimited travel for one week (total cost)"""
    senior_pass_28_to_69_days: float
    """Senior fare, per day, for unlimited travel for 28 to 69 days"""
    senior_pass_70_plus_days: float
    """Senior fare, per day, for unlimited travel for 70 to 325 days; passes for 326 to 365 days cost the same total amount as a 325-day pass"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list[dict] | dict | None) -> Self:
        early_bird_travel = kwargs.pop("IsEarlyBird")
        free_fare_zone = kwargs.pop("IsJourneyInFreeTramZone")
        weekend = kwargs.pop("IsThisWeekendJourney")
        zones = kwargs.pop("ZoneInfo")["UniqueZones"]
        fares = kwargs.pop("PassengerFares")

        assert fares[0]["PassengerType"] == "fullFare"
        full_2_hour_peak = fares[0]["Fare2HourPeak"]
        full_2_hour_off_peak = fares[0]["Fare2HourOffPeak"]
        full_weekday_cap_peak = fares[0]["FareDailyPeak"]
        full_weekday_cap_off_peak = fares[0]["FareDailyOffPeak"]
        full_weekend_cap = fares[0]["WeekendCap"]
        full_holiday_cap = fares[0]["HolidayCap"]
        full_pass_7_days_total = fares[0]["Pass7Days"]
        full_pass_28_to_69_days = fares[0]["Pass28To69DayPerDay"]
        full_pass_70_plus_days = fares[0]["Pass70PlusDayPerDay"]

        assert fares[1]["PassengerType"] == "concession"
        concession_2_hour_peak = fares[1]["Fare2HourPeak"]
        concession_2_hour_off_peak = fares[1]["Fare2HourOffPeak"]
        concession_weekday_cap_peak = fares[1]["FareDailyPeak"]
        concession_weekday_cap_off_peak = fares[1]["FareDailyOffPeak"]
        concession_weekend_cap = fares[1]["WeekendCap"]
        concession_holiday_cap = fares[1]["HolidayCap"]
        concession_pass_7_days_total = fares[1]["Pass7Days"]
        concession_pass_28_to_69_days = fares[1]["Pass28To69DayPerDay"]
        concession_pass_70_plus_days = fares[1]["Pass70PlusDayPerDay"]

        assert fares[2]["PassengerType"] == "senior"
        senior_2_hour_peak = fares[2]["Fare2HourPeak"]
        senior_2_hour_off_peak = fares[2]["Fare2HourOffPeak"]
        senior_weekday_cap_peak = fares[2]["FareDailyPeak"]
        senior_weekday_cap_off_peak = fares[2]["FareDailyOffPeak"]
        senior_weekend_cap = fares[2]["WeekendCap"]
        senior_holiday_cap = fares[2]["HolidayCap"]
        senior_pass_7_days_total = fares[2]["Pass7Days"]
        senior_pass_28_to_69_days = fares[2]["Pass28To69DayPerDay"]
        senior_pass_70_plus_days = fares[2]["Pass70PlusDayPerDay"]

        return cls(early_bird_travel=early_bird_travel, free_fare_zone=free_fare_zone, weekend=weekend, zones=zones, full_2_hour_peak=full_2_hour_peak, full_2_hour_off_peak=full_2_hour_off_peak, full_weekday_cap_peak=full_weekday_cap_peak, full_weekday_cap_off_peak=full_weekday_cap_off_peak, full_weekend_cap=full_weekend_cap, full_holiday_cap=full_holiday_cap, full_pass_7_days_total=full_pass_7_days_total, full_pass_28_to_69_days=full_pass_28_to_69_days, full_pass_70_plus_days=full_pass_70_plus_days, concession_2_hour_peak=concession_2_hour_peak, concession_2_hour_off_peak=concession_2_hour_off_peak, concession_weekday_cap_peak=concession_weekday_cap_peak, concession_weekday_cap_off_peak=concession_weekday_cap_off_peak, concession_weekend_cap=concession_weekend_cap, concession_holiday_cap=concession_holiday_cap, concession_pass_7_days_total=concession_pass_7_days_total, concession_pass_28_to_69_days=concession_pass_28_to_69_days, concession_pass_70_plus_days=concession_pass_70_plus_days, senior_2_hour_peak=senior_2_hour_peak, senior_2_hour_off_peak=senior_2_hour_off_peak, senior_weekday_cap_peak=senior_weekday_cap_peak, senior_weekday_cap_off_peak=senior_weekday_cap_off_peak, senior_weekend_cap=senior_weekend_cap, senior_holiday_cap=senior_holiday_cap, senior_pass_7_days_total=senior_pass_7_days_total, senior_pass_28_to_69_days=senior_pass_28_to_69_days, senior_pass_70_plus_days=senior_pass_70_plus_days, **kwargs)


@dataclass(kw_only=True, slots=True)
class SearchResult(TimetableData):
    """Response from an API search request."""

    stops: list[Stop]
    """Stops matching the search parameters"""
    routes: list[Route]
    """Routes matching the search parameters"""
    outlets: list[Outlet]
    """Outlets matching the search parameters, if requested; [] (empty list) otherwise"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        stops = [Stop.load(**item) for item in kwargs.pop("stops")]
        routes = [Route.load(**item) for item in kwargs.pop("routes")]
        outlets = [Outlet.load(**item) for item in kwargs.pop("outlets")]
        kwargs.pop("status")
        return cls(stops=stops, routes=routes, outlets=outlets)


class TimetableAPI:
    """Interface class with the PTV Timetable API."""

    def __init__(self: Self, dev_id: str | int, key: str) -> None:
        """Initialises a new PTVAPI instance with the supplied credentials.

        :param dev_id: User ID
        :param key: API request signing key (a UUID)
        :return: ``None``
        """
        
        if type(dev_id) not in (str, int):
            raise TypeError(f"devID must be str or int, not {type(dev_id).__name__}")
        elif type(key) is not str:
            raise TypeError(f"key must be str, not {type(key).__name__}")

        if UUID_PATTERN.fullmatch(key) is None:
            raise ValueError(f"key is not a UUID string: {key}")

        self._dev_id: Final[str] = str(dev_id)
        """API user ID"""
        self._key: Final[bytes] = key.encode(encoding="ascii")
        """API request signing key"""

        _logger.info("PTVAPI instance created")
        return

    def __del__(self: Self) -> None:
        """
        Logs the prospective deletion of an instance into the module logger.

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

    @sleep_and_retry
    @limits(calls=1, period=10)  # 1 call every 10 seconds
    def call(self: Self, request: str) -> dict[str, _Record | list[_Record]]:
        """Make the request to the API and format the result.

        :param request: API request string
        :return: Result of API request as a ``dict``
        """

        url = self._encode_url(request)
        _logger.debug("Requesting from: " + url)
        r = requests.get(url)
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

    def list_directions(self: Self, direction_id: int, route_type: RouteType | None = None) -> list[Direction]:
        """Returns all directions of travel in the database with the specified identifier for all (or the specified) route type(s).

        :param direction_id: The direction identifier
        :param route_type: Return only the directions with the specified route type
        :return: List of directions
        """

        req = f"/v3/directions/{direction_id}" + ("/route_type/{route_type}" if route_type is not None else "")
        return [Direction.load(**item) for item in self.call(req)["directions"]]

    def get_pattern(self: Self,
                    run_ref: str,
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
                run_ref: str,
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
