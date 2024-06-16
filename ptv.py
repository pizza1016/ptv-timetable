from collections.abc import Iterable
from dataclasses import dataclass, InitVar
from datetime import datetime, timezone
from hashlib import sha1
from hmac import HMAC
from ratelimit import limits, sleep_and_retry
from sys import stdout
from typing import Final, Literal, overload, Self
from zoneinfo import ZoneInfo
import logging
import platform
import re
import requests
if platform.system() == "Windows":
    # noinspection PyUnresolvedReferences
    import tzdata

__all__ = ["APIClient", "MET_TRAIN", "METRO", "TRAM", "BUS", "REG_TRAIN", "COACH", "VLINE", "ALL", "STOP", "ROUTE", "RUN", "DIRECTION", "DISRUPTION", "VEHICLE_DESCRIPTOR", "VEHICLE_POSITION", "NONE"]

type _Values = str | int | float | bool | datetime | _Record
type _Record = dict[str, _Values | dict[str, _Values] | list[_Values]]

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


class APIData:
    pass


@dataclass(kw_only=True)
class PathGeometry(APIData):
    """Represents the physical geometry of the attached route or run."""

    direction_id: int
    """Identifier of the direction of travel represented by this geometry"""
    valid_from: str
    """Date geometry is valid from"""
    valid_to: str
    """Date geometry is valid to"""
    paths: list[str]
    """Strings of coordinate pairs that draws the path"""


@dataclass(kw_only=True)
class StopTicket(APIData):
    """Ticketing information for the attached stop."""

    ticket_type: Literal["myki", "paper", "both"]
    """Whether this stop uses myki ticketing, paper ticketing, or both"""
    zone: str
    """Description of the ticketing zone"""
    is_free_fare_zone: bool
    """Whether this stop is in a free fare zone"""
    ticket_machine: bool
    """Whether this stop has ticket machines"""
    ticket_checks: bool
    """"""  # TODO purpose unclear
    vline_reservation: bool
    """"""  # TODO unsure if this is "need reservation to access" or "reservation facilities available here"
    ticket_zones: list[int]
    """Ticketing zone(s) this stop is in"""


@dataclass(kw_only=True)
class StopContact(APIData):
    lost_property_contact_number: str | None
    phone: str | None
    lost_property: str | None
    feedback: str | None


@dataclass(kw_only=True)
class StopLocation(APIData):
    postcode: int
    municipality: str
    municipality_id: int
    primary_stop_name: str
    road_type_primary: str
    second_stop_name: str
    road_type_second: str
    bay_number: int
    bay_nbr: InitVar[int]
    locality: str
    suburb: InitVar[str]
    latitude: float
    longitude: float
    gps: InitVar[dict[Literal["latitude", "longitude"], float]]

    def __post_init__(self: Self, bay_nbr: int, suburb: str, gps: dict[Literal["latitude", "longitude"], float]) -> None:
        self.bay_number = bay_nbr
        self.locality = suburb
        self.latitude = gps["latitude"]
        self.longitude = gps["longitude"]
        return


@dataclass(kw_only=True)
class StopAmenities(APIData):
    seat_type: str
    pay_phone: bool
    indoor_waiting_area: bool
    sheltered_waiting_area: bool
    bicycle_rack: int
    bicycle_cage: bool
    bicycle_locker: int
    luggage_locker: int
    kiosk: bool
    seat: str
    stairs: str
    baby_change_facility: str
    parkiteer: None
    replacement_bus_stop_loc: str
    QTEM: None
    bike_storage: None
    PID: bool
    ATM: None
    travellers_aid: bool
    premium_stop: None
    PSOs: None
    melb_bike_share: None
    luggage_storage: None
    luggage_check_in: None
    toilet: bool
    taxi_rank: bool
    car_parking: str
    cctv: bool


@dataclass(kw_only=True)
class Wheelchair(APIData):
    accessible_ramp: bool
    parking: bool
    telephone: bool
    toilet: bool
    low_ticket_counter: None
    manoeuvring: None
    manouvering: InitVar[None]
    raised_platform: None
    ramp: None
    secondary_path: None
    raised_platform_shelter: None
    raised_platform_shelther: InitVar[None]
    steep_ramp: None

    def __post_init__(self: Self, manouvering: None, raised_platform_shelther: None) -> None:
        self.manoeuvring = manouvering
        self.raised_platform_shelter = raised_platform_shelther
        return


@dataclass(kw_only=True)
class StopAccessibility(APIData):
    lighting: bool
    platform_number: None
    audio_customer_information: None
    escalator: bool
    hearing_loop: bool
    lift: bool
    stairs: bool
    stop_accessible: None
    tactile_ground_surface_indicator: bool
    waiting_room: None
    wheelchair: Wheelchair
    wheelchair: InitVar[dict[str, bool | None]]

    def __post_init__(self: Self, wheelchair: dict[str, bool | None]) -> None:
        self.wheelchair = Wheelchair(**wheelchair)
        return


@dataclass(kw_only=True)
class StopStaffing(APIData):
    mon_am_from: str
    mon_am_to: str
    mon_pm_from: str
    mon_pm_to: str
    tue_am_from: str
    tue_am_to: str
    tue_pm_from: str
    tue_pm_to: str
    wed_am_from: str
    wed_am_to: str
    wed_pm_from: str
    wed_pm_to: str
    wed_pm_To: InitVar[str]
    thu_am_from: str
    thu_am_to: str
    thu_pm_from: str
    thu_pm_to: str
    fri_am_from: str
    fri_am_to: str
    fri_pm_from: str
    fri_pm_to: str
    sat_am_from: str
    sat_am_to: str
    sat_pm_from: str
    sat_pm_to: str
    sun_am_from: str
    sun_am_to: str
    sun_pm_from: str
    sun_pm_to: str
    ph_from: str
    ph_to: str
    ph_additional_text: str

    def __post_init__(self: Self, wed_pm_To: str) -> None:
        self.wed_pm_to = wed_pm_To
        return


@dataclass(kw_only=True)
class Route(APIData):
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
    geopath: InitVar[list[dict] | None]
    route_service_status: dict[Literal["description", "timestamp"], str]
    """Service status of the route"""

    def __post_init__(self: Self, geopath: list[dict] | None = None) -> None:
        self.route_name = self.route_name.strip()
        if self.geometry is None and geopath is not None:
            self.geometry = [PathGeometry(**item) for item in geopath]
        return


@dataclass(kw_only=True)
class Stop(APIData):
    """Represents a particular transport stop."""

    stop_id: int
    """Identifier of this stop"""
    route_type: int
    """Identifier of the travel mode of this stop"""
    stop_name: str
    """Name of this stop"""
    locality: str
    """Locality (suburb/town) this stop is in"""
    stop_suburb: InitVar[str]
    stop_latitude: float
    """Latitude coordinate of the stop's location"""
    stop_longitude: float
    """Longitude coordinate of the stop's location"""
    stop_distance: float | None = None
    """If a location was specified in the API call, distance in metres between this stop and that location; otherwise, 0.0 or None"""
    stop_landmark: str
    """Notable landmarks near the stop; "" (empty string) if none"""
    stop_sequence: int | None = None
    """Sort key for this stop along a route or run that is the subject of the API call; if neither were provided, value is 0"""
    stop_ticket: StopTicket | None = None
    """Ticketing information for this stop; None if the API response did not return this information"""
    stop_ticket: InitVar[dict | None]

    # From /v3/stops/...
    point_id: int | None = None
    """Identifier of this stop in the PTV static timetable dump; None if the API operation doesn't use this field"""  # TODO: presumably
    disruption_ids: list[int] | None = None
    """Current or future disruptions affecting this stop; None if the API operation doesn't use this field"""
    routes: list[Route] | None = None
    """List of routes serving this stop; None if the API operation doesn't use this field"""
    operating_hours: str | None = None
    """Description of railway station opening hours; None if the API operation doesn't use this field"""
    mode_id: int | None = None
    """"""  # TODO
    station_details_id: int | None = None
    """"""  # TODO
    flexible_stop_opening_hours: str | None = None
    """"""  # TODO
    stop_contact: StopContact | None = None
    """Operator contact information for this stop; None if not requested from API"""
    stop_contact: InitVar[dict[str, str | None] | None]
    stop_location: StopLocation | None = None
    """Location information about this stop; None if not requested from API"""
    stop_location: InitVar[dict[str, str | int | dict[str, float]] | None]
    stop_amenities: StopAmenities | None = None
    """Facilities available at this stop; None if not requested from API"""
    stop_amenities: InitVar[dict[str, str | bool | None] | None]
    stop_accessibility: StopAccessibility | None = None
    """Information about accessibility features available at this stop; None if not requested from API"""
    stop_accessibility: InitVar[dict[str, bool | dict[str, bool | None] | None]]
    stop_staffing: StopStaffing | None = None
    """Staffing information for this stop; None if not requested from API"""
    stop_staffing: InitVar[dict[str, str] | None]
    station_type: str | None = None
    """"""  # TODO
    station_description: str | None = None
    """"""  # TODO

    def __post_init__(self: Self, stop_suburb: str, stop_ticket: dict | None = None, stop_contact: dict[str, str | None] | None = None, stop_location: dict[str, str | int | dict[str, float]] | None = None, stop_amenities: dict[str, str | bool | None] | None = None, stop_accessibility: dict[str, bool | dict[str, bool | None] | None] = None, stop_staffing: dict[str, str] | None = None) -> None:
        self.stop_name = self.stop_name.strip()
        if not hasattr(self, "locality"):
            self.locality = stop_suburb
        if self.stop_ticket is None and stop_ticket is not None:
            self.stop_ticket = StopTicket(**stop_ticket)
        if self.stop_contact is None and stop_contact is not None:
            self.stop_contact = StopContact(**stop_contact)
        if self.stop_location is None and stop_location is not None:
            self.stop_location = StopLocation(**stop_location)
        if self.stop_amenities is None and stop_amenities is not None:
            self.stop_amenities = StopAmenities(**stop_amenities)
        if self.stop_accessibility is None and stop_accessibility is not None:
            self.stop_accessibility = StopAccessibility(**stop_amenities)
        if self.stop_staffing is None and stop_staffing is not None:
            self.stop_staffing = StopStaffing(**stop_staffing)
        return


@dataclass(kw_only=True)
class Departure(APIData):
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
    scheduled_departure_utc: InitVar[str]
    estimated_departure: datetime | None
    """Estimated real-time departure time; None if real-time departure time is unavailable"""
    estimated_departure_utc: InitVar[str | None]
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
    skipped_stops: InitVar[list[dict] | None]

    def __post_init__(self: Self, scheduled_departure_utc: str, estimated_departure_utc: str | None, skipped_stops: list[dict] | None = None) -> None:
        if not hasattr(self, "scheduled_departure"):
            self.scheduled_departure = datetime.fromisoformat(scheduled_departure_utc).astimezone(TZ_MELBOURNE)
        if not hasattr(self, "estimated_departure"):
            self.estimated_departure = datetime.fromisoformat(estimated_departure_utc).astimezone(TZ_MELBOURNE) if estimated_departure_utc is not None else None
        if self.skipped_stops is None:
            self.skipped_stops = [Stop(**item) for item in skipped_stops] if skipped_stops is not None else None
        return


@dataclass(kw_only=True)
class VehiclePosition(APIData):
    """Represents the position of the attached vehicle."""

    latitude: float | None
    """Latitude coordinate of the vehicle's position for buses; None if this information is unavailable"""
    longitude: float | None
    """Longitude coordinate of the vehicle's position for buses; None if this information is unavailable"""
    easting: float | None
    """Latitude coordinate of the vehicle's position for metropolitan trains; None if this information is unavailable"""
    northing: float | None
    """Longitude coordinate of the vehicle's position for metropolitan trains; None if this information is unavailable"""
    direction: str  # TODO
    bearing: float | None
    """Vehicle's current direction of travel in degrees clockwise from geographic north; None if this information is unavailable"""
    supplier: str
    """Source of vehicle information"""
    as_of: datetime | None
    """Date and time at which this position information is current"""
    datetime_utc: InitVar[str | None]
    expires: datetime | None
    """Date and time at which this position information is no longer valid"""
    expiry_time: InitVar[str | None]

    def __post_init__(self: Self, datetime_utc: str, expiry_time: str) -> None:
        if not hasattr(self, "as_of"):
            self.as_of = datetime.fromisoformat(datetime_utc).astimezone(TZ_MELBOURNE)
        if not hasattr(self, "expires"):
            self.expires = datetime.fromisoformat(expiry_time).astimezone(TZ_MELBOURNE)
        return


@dataclass(kw_only=True)
class VehicleDescriptor(APIData):
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


@dataclass(kw_only=True)
class Run(APIData):
    """Represents a particular run or service along a route."""

    run_ref: str
    """Identifier of this run"""
    route_id: int
    """Identifier of the route this run belongs to"""
    route_type: int
    """Identifier of the travel mode of this run"""
    final_stop_id: int
    """Identifier of the terminating stop of this run"""
    destination_name: str
    """Public-facing destination name of this run"""
    status: str
    """Status of this metropolitan train service; "scheduled" for all other modes"""
    direction_id: int
    """Identifier of the direction of travel of this run"""
    run_sequence: int
    """Sort key for this run in a chronological list of runs for this route and direction of travel"""
    express_stop_count: int
    """Number of skipped stops in this run"""
    vehicle_position: VehiclePosition | None
    """Real-time vehicle position information where available; None if this information was not requested from the API"""
    vehicle_position: InitVar[dict | None]
    vehicle_descriptor: VehicleDescriptor | None
    """Information on the vehicle operating this service, where available; None if this information was not requested from the API"""
    vehicle_descriptor: InitVar[dict | None]
    geometry: list[PathGeometry]
    """Physical geometry of this run's journey; [] (empty list) if not requested from API"""
    geopath: InitVar[list[dict[str, str | int | list[str]]]]
    interchange: dict | None
    """Indicates, if any, the run this service will operate after terminating; None if this information was not requested from the API"""

    run_id: InitVar[int | None]

    def __post_init__(self: Self, vehicle_position: dict | None, vehicle_descriptor: dict | None, geopath: list[dict[str, str | int | list[str]]], run_id: int | None = None):
        self.destination_name = self.destination_name.strip()
        if not hasattr(self, "geometry"):
            self.geometry = [PathGeometry(**item) for item in geopath]
        if not hasattr(self, "vehicle_position"):
            self.vehicle_position = VehiclePosition(**vehicle_position) if vehicle_position is not None else None
        if not hasattr(self, "vehicle_descriptor"):
            self.vehicle_descriptor = VehicleDescriptor(**vehicle_descriptor) if vehicle_descriptor is not None else None
        # noinspection PyStatementEffect
        run_id
        return


@dataclass(kw_only=True)
class Direction(APIData):
    """Represents a direction of travel on a particular route."""

    direction_id: int
    """Identifier for direction of travel"""
    direction_name: str
    """Name of direction of travel"""
    route_direction_description: str
    """Detailed description of this direction of travel along this route, as publicly displayed on the PTV website"""
    route_id: int
    """Identifier for the route specified by this direction of travel"""
    route_type: int
    """Identifier for the mode of travel of this route and destination"""


@dataclass(kw_only=True)
class Disruption(APIData):
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
    published_on: InitVar[str]
    last_updated: datetime
    """Date and time information about this disruption was last updated"""
    last_updated: InitVar[str]
    from_date: datetime
    """Date and time this disruption began/will begin"""
    from_date: InitVar[str]
    to_date: datetime | None
    """Date and time this disruption will end; None if unknown or uncertain"""
    to_date: InitVar[str | None]
    routes: list[Route]
    """Routes affected by this disruption"""
    routes: InitVar[list[dict]]
    stops: list[Stop]
    """Stops affected by this disruption"""
    stops: InitVar[list[dict]]
    colour: str
    """Hex code for the alert colour on the disruption website"""
    display_on_board: bool
    """Indicates if this disruption is displayed on the PTV disruption boards across the network"""
    display_status: bool
    """Indicates if this disruption updates the service status of the affected routes on the disruption boards (presumably)"""

    def __post_init__(self: Self, published_on: str, last_updated: str, from_date: str, to_date: str | None, routes: list[dict], stops: list[dict]) -> None:
        self.published_on = datetime.fromisoformat(published_on).astimezone(TZ_MELBOURNE)
        self.last_updated = datetime.fromisoformat(last_updated).astimezone(TZ_MELBOURNE)
        self.from_date = datetime.fromisoformat(from_date).astimezone(TZ_MELBOURNE)
        self.to_date = datetime.fromisoformat(to_date).astimezone(TZ_MELBOURNE) if to_date is not None else None
        self.routes = [Route(**item) for item in routes]
        self.stops = [Stop(**item) for item in stops]
        return


@dataclass(kw_only=True)
class StoppingPattern(APIData):
    """Represents a stopping pattern for a particular run. Sequence specified in 'departures' field."""

    disruptions: list[Disruption]
    """List of disruptions affecting this run or the relevant routes and stops"""
    disruptions: InitVar[list[dict]]
    departures: list[Departure]
    """Sequence of departures from stops made by this run"""
    departures: InitVar[list[dict]]
    stops: dict[int, Stop]
    """Mapping of the relevant stop identifiers to Stop objects"""
    stops: InitVar[dict[str, dict]]
    routes: dict[int, Route]
    """Mapping of the relevant route identifiers to Route objects"""
    routes: InitVar[dict[str, dict]]
    runs: dict[str, Run]
    """Mapping of the relevant run identifiers to Run objects"""
    runs: InitVar[dict[str, dict]]
    directions: dict[int, Direction]
    """Mapping of the relevant travel direction identifiers to Direction objects"""
    directions: InitVar[dict[str, dict]]

    def __post_init__(self: Self, disruptions: list[dict], departures: list[dict], stops: dict[str, dict], routes: dict[str, dict], runs: dict[str, dict], directions: dict[str, dict]) -> None:
        self.disruptions = [Disruption(**item) for item in disruptions]
        self.departures = [Departure(**item) for item in departures]
        self.stops = {int(key): Stop(**value) for key, value in stops.items()}
        self.routes = {int(key): Route(**value) for key, value in routes.items()}
        self.runs = {key: Run(**value) for key, value in runs.items()}
        self.directions = {int(key): Direction(**value) for key, value in directions.items()}
        return


@dataclass(kw_only=True)
class DeparturesResponse(APIData):
    """Response from the departures API request; also contains any relevant route, service and stop details."""

    departures: list[Departure]
    """Departures returned from the API request"""
    departures: InitVar[list[dict]]
    stops: dict[int, Stop]
    """Mapping of stop identifiers to stop objects related to the returned departures"""
    stops: InitVar[dict[str, dict]]
    routes: dict[int, Route]
    """Mapping of route identifiers to route objects related to the returned departures"""
    routes: InitVar[dict[str, dict]]
    runs: dict[str, Run]
    """Mapping of run identifiers to run objects related to the returned departures"""
    runs: InitVar[dict[str, dict]]
    directions: dict[int, Direction]
    """Mapping of direction identifiers to direction objects related to the returned departures"""
    directions: InitVar[dict[str, dict]]
    disruptions: dict[int, Disruption]
    """Mapping of disruption identifiers to disruption objects related to the returned departures"""
    disruptions: InitVar[dict[str, dict]]

    status: InitVar[dict[str, str | int]]

    def __post_init__(self: Self, departures: list[dict], stops: dict[str, dict], routes: dict[str, dict], runs: dict[str, dict], directions: dict[str, dict], disruptions: dict[str, dict], status: dict[str, str | int]) -> None:
        self.departures = [Departure(**item) for item in departures]
        self.stops = {int(key): Stop(**value) for key, value in stops.items()}
        self.routes = {int(key): Route(**value) for key, value in routes.items()}
        self.runs = {key: Run(**value) for key, value in runs.items()}
        self.directions = {int(key): Direction(**value) for key, value in directions.items()}
        self.disruptions = {int(key): Disruption(**value) for key, value in disruptions.items()}
        # noinspection PyStatementEffect
        status
        return


@dataclass(kw_only=True)
class Outlet(APIData):
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
    outlet_name: InitVar[str]
    locality: str
    """Locality/suburb/town of the outlet"""
    outlet_suburb: InitVar[str]
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

    def __post_init__(self: Self, outlet_name: str, outlet_suburb: str) -> None:
        self.street_address = outlet_name
        self.locality = outlet_suburb
        return


@dataclass(kw_only=True)
class FareEstimate(APIData):
    """Fare estimate for the specified travel. All fares in AUD."""

    early_bird_travel: bool
    """Whether the touch on and off are made at metropolitan train stations on a non-public-holiday weekday before 7:15 am Melbourne time"""
    IsEarlyBird: InitVar[bool]
    free_fare_zone: bool
    """Whether this journey is entirely within a free fare zone"""
    IsJourneyInFreeTramZone: InitVar[bool]
    weekend: bool
    """Whether this journey is made on a weekend or public holiday"""
    zones: list[int]
    """List of fare zones this fare estimate is valid for"""
    ZoneInfo: InitVar[dict[str, int | list[int]]]

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
    concession_weekday_cap_peak: float
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
    PassengerFares: InitVar[list[dict[str, str | float]]]

    # noinspection PyPep8Naming,PyShadowingNames
    def __post_init__(self: Self, IsEarlyBird: bool, IsJourneyInFreeTramZone: bool, ZoneInfo: dict[str, int | list[int]], PassengerFares: list[dict[str, str | float]]) -> None:
        self.early_bird_travel = IsEarlyBird
        self.free_fare_zone = IsJourneyInFreeTramZone
        self.zones = ZoneInfo["UniqueZones"]

        for item in PassengerFares:
            if item["PassengerType"] == "fullFare":
                self.full_2_hour_peak = item["Fare2HourPeak"]
                self.full_2_hour_off_peak = item["Fare2HourOffPeak"]
                self.full_weekday_cap_peak = item["FareDailyPeak"]
                self.full_weekday_cap_off_peak = item["FareDailyOffPeak"]
                self.full_weekend_cap = item["WeekendCap"]
                self.full_holiday_cap = item["HolidayCap"]
                self.full_pass_7_days_total = item["Pass7Days"]
                self.full_pass_28_to_69_days = item["Pass28To69DayPerDay"]
                self.full_pass_70_plus_days = item["Pass70PlusDayPerDay"]
            elif item["PassengerType"] == "concession":
                self.concession_2_hour_peak = item["Fare2HourPeak"]
                self.concession_2_hour_off_peak = item["Fare2HourOffPeak"]
                self.concession_weekday_cap_peak = item["FareDailyPeak"]
                self.concession_weekday_cap_off_peak = item["FareDailyOffPeak"]
                self.concession_weekend_cap = item["WeekendCap"]
                self.concession_holiday_cap = item["HolidayCap"]
                self.concession_pass_7_days_total = item["Pass7Days"]
                self.concession_pass_28_to_69_days = item["Pass28To69DayPerDay"]
                self.concession_pass_70_plus_days = item["Pass70PlusDayPerDay"]
            elif item["PassengerType"] == "senior":
                self.senior_2_hour_peak = item["Fare2HourPeak"]
                self.senior_2_hour_off_peak = item["Fare2HourOffPeak"]
                self.senior_weekday_cap_peak = item["FareDailyPeak"]
                self.senior_weekday_cap_off_peak = item["FareDailyOffPeak"]
                self.senior_weekend_cap = item["WeekendCap"]
                self.senior_holiday_cap = item["HolidayCap"]
                self.senior_pass_7_days_total = item["Pass7Days"]
                self.senior_pass_28_to_69_days = item["Pass28To69DayPerDay"]
                self.senior_pass_70_plus_days = item["Pass70PlusDayPerDay"]
        return


@dataclass(kw_only=True)
class SearchResult(APIData):
    """Response from an API search request."""

    stops: list[Stop]
    """Stops matching the search parameters"""
    stops: InitVar[list[dict]]
    routes: list[Route]
    """Routes matching the search parameters"""
    routes: InitVar[list[dict]]
    outlets: list[Outlet]
    """Outlets matching the search parameters, if requested; [] (empty list) otherwise"""
    outlets: InitVar[list[dict]]

    status: InitVar[dict[str, str | int]]

    def __post_init__(self: Self, stops: list[dict], routes: list[dict], outlets: list[dict], status: dict[str, str | int]) -> None:
        self.stops = [Stop(**item) for item in stops]
        self.routes = [Route(**item) for item in routes]
        self.outlets = [Outlet(**item) for item in outlets]
        # noinspection PyStatementEffect
        status
        return


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

    def list_route_directions(self: Self, route_id: int) -> list[Direction]:
        """Returns the directions of travel for a particular route.

        :param route_id: The route ID number
        :return: A list of directions
        """

        return [Direction(**item) for item in self.call(f"/v3/directions/route/{route_id}")["directions"]]

    def list_directions(self: Self, direction_id: int, route_type: RouteType | None = None) -> list[Direction]:
        """Returns all directions of travel in the database with the specified identifier for all (or the specified) route type(s).

        :param direction_id: The direction ID number
        :param route_type: Return only the directions with the specified route type
        :return: A list of directions
        """

        req = f"/v3/directions/{direction_id}" + ("/route_type/{route_type}" if route_type is not None else "")
        return [Direction(**item) for item in self.call(req)["directions"]]

    def get_pattern(self: Self,
                    run_ref: str,
                    route_type: RouteType,
                    stop_id: int | None = None,
                    date: datetime | str | None = None,
                    include_skipped_stops: bool | None = None,
                    expand: ExpandType | Iterable[ExpandType] = NONE,
                    include_geopath: bool | None = None
                    ) -> StoppingPattern:
        """Returns the stopping pattern of the specified run of the specified route type.

        :param run_ref: The run identifier
        :param route_type: The run's travel mode identifier
        :param stop_id: Include only the stop with the specified stop ID
        :param date: TODO
        :param include_skipped_stops: Include a list of stops that are skipped by the pattern (server default is False)
        :param expand: TODO
        :param include_geopath: Include the pattern's path geometry (server default is False)
        :return: The stopping pattern of the specified run
        """

        req = f"/v3/pattern/run/{run_ref}/route_type/{route_type}"

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("stop_id", stop_id, "date_utc", date.astimezone(timezone.utc).isoformat(), "include_skipped_stops", include_skipped_stops, "expand", expand, "include_geopath", include_geopath, s=req)

        res = self.call(req)
        return StoppingPattern(**res)

    def get_route(self: Self, route_id: int, include_geopath: bool | None = None, geopath_utc: str | None = None) -> Route:
        """Returns the details of the route with the specified route identifier.

        :param route_id: The route identifier
        :param include_geopath: Include the route's path geometry (server default is False)
        :param geopath_utc: Retrieve the path geometry valid at the specified date (ISO 8601 formatted)
        :return: Details of the specified route
        """

        req = self.build_arg_string("include_geopath", include_geopath, "geopath_utc", geopath_utc, s=f"/v3/routes/{route_id}")
        return Route(**self.call(req)["route"])

    def list_routes(self: Self, route_types: Iterable[RouteType] | None = None, route_name: str | None = None) -> list[Route]:
        """Returns all routes of all (or specified) types.

        :param route_types: Return only the routes of the specified type(s)
        :param route_name: Return the routes with names containing the specified substring
        :return: A list of routes
        """

        req = self.build_arg_string("route_types", route_types, "route_name", route_name, s="/v3/routes")
        return [Route(**item) for item in self.call(req)["routes"]]

    def list_route_types(self: Self) -> list[dict[str, str | int]]:
        """Returns the names and identifiers of all route types.

        Returned records contain these fields:
        "route_type_name" (str): Name of the route type
        "route_type" (int): Value representing the route type

        :return: A list of records containing the aforementioned fields
        """

        return self.call("/v3/route_types")["route_types"]

    def get_run(self: Self,
                run_ref: str,
                route_type: RouteType | None = None,
                expand: ExpandType = NONE,
                date: datetime | str | None = None,
                include_geopath: bool | None = None
                ) -> list[Run]:
        """Returns a list of all runs with the specified run identifier and, optionally, the specified route type.

        :param run_ref: The run identifier
        :param route_type: Return runs of the specified type only
        :param expand: Optional data to include in returned list
        :param date: Return only data from the specified date
        :param include_geopath: Include the run's path geometry (server default is false)
        :return: A list of runs (this will still be a list even if there's only one exact match)
        """

        req = f"/v3/runs/{run_ref}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("expand", expand, "include_geopath", include_geopath, "date_utc", date.astimezone(timezone.utc).isoformat(), s=req)

        return [Run(**item) for item in self.call(req)["runs"]]

    def list_runs(self: Self,
                  route_id: int,
                  route_type: RouteType | None = None,
                  expand: ExpandType | Iterable[ExpandType] = NONE,
                  date: datetime | str | None = None
                  ) -> list[Run]:
        """Returns a list of all runs for the specified route identifier and, if provided, the specified route type.

        :param route_id: The route identifier
        :param route_type: The transport type of the specified route
        :param expand: Optional data to include in the response
        :param date: Return only data from the specified date
        :return: A list of runs
        """

        req = f"/v3/runs/route/{route_id}" + (f"/route_type/{route_type}" if route_type is not None else "")

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = self.build_arg_string("expand", expand, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, s=req)

        return [Run(**item) for item in self.call(req)["runs"]]

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
        """
        Returns the stop with the specified stop identifier and route type.

        :param stop_id: The stop identifier
        :param route_type: The transport type of the specified stop
        :param stop_location: Whether to include stop location information in the result (server default is False)
        :param stop_amenities: Whether to include stop amenities information in the result (server default is False)
        :param stop_accessibility: Whether to include stop accessibility information in the result (server default is False)
        :param stop_contact: Whether to include operator contact details in the result (server default is False)
        :param stop_ticket: Whether to include ticketing information in the result (server default is False)
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is False)
        :param stop_staffing: Whether to include stop staffing information in the result (server default is False)
        :param stop_disruptions: Whether to include information about disruptions affecting the stop in the result (server default is False)
        :return: Details of the specified stop
        """
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
        """
        Returns the stop with the specified stop identifier and route type.

        :param stop_id: The stop identifier
        :param route_type: The transport type of the specified stop
        :param stop_location: Whether to include stop location information in the result (server default is False)
        :param stop_amenities: Whether to include stop amenities information in the result (server default is False)
        :param stop_accessibility: Whether to include stop accessibility information in the result (server default is False)
        :param stop_contact: Whether to include operator contact details in the result (server default is False)
        :param stop_ticket: Whether to include ticketing information in the result (server default is False)
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is False)
        :param stop_staffing: Whether to include stop staffing information in the result (server default is False)
        :param stop_disruptions: Whether to include information about disruptions affecting the stop in the result (server default is False)
        :return: Details of the specified stop
        """
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
        """
        Returns the stop with the specified stop identifier and route type.

        :param stop_id: The stop identifier
        :param route_type: The transport type of the specified stop
        :param stop_location: Whether to include stop location information in the result (server default is False)
        :param stop_amenities: Whether to include stop amenities information in the result (server default is False)
        :param stop_accessibility: Whether to include stop accessibility information in the result (server default is False)
        :param stop_contact: Whether to include operator contact details in the result (server default is False)
        :param stop_ticket: Whether to include ticketing information in the result (server default is False)
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is False)
        :param stop_staffing: Whether to include stop staffing information in the result (server default is False)
        :param stop_disruptions: Whether to include information about disruptions affecting the stop in the result (server default is False)
        :return: Details of the specified stop
        """
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

        req = f"/v3/stops/{stop_id}/route_type/{route_type}"
        req = self.build_arg_string("stop_location", stop_location, "stop_amenities", stop_amenities, "stop_accessibility", stop_accessibility, "stop_contact", stop_contact, "stop_ticket", stop_ticket, "gtfs", gtfs, "stop_staffing", stop_staffing, "stop_disruptions", stop_disruptions, s=req)

        res = self.call(req)["stop"]
        return Stop(**res)

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
        return [Stop(**item) for item in self.call(req)["stops"]]

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
        :param stop_disruptions: Whether to include stop disruption information (server default is False)
        :return: A list of stops in the specified search parameters
        """

        req = f"/v3/stops/location/{latitude},{longitude}"
        req = self.build_arg_string("route_types", route_types, "max_results", max_results, "max_distance", max_distance, "stop_disruptions", stop_disruptions, s=req)

        return [Stop(**item) for item in self.call(req)["stops"]]

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

    # platform_numbers is specified by keyword
    # gtfs is not specified
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int,
                        route_id: None = None,
                        *,
                        platform_numbers: Iterable[str | int],
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

    # platform_numbers is specified by position - require explicit None on route_id
    # also for when both parameters are None
    # gtfs is not specified
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: int,
                        route_id: None,
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

    # platform_numbers is specified by keyword; requires gtfs to be specified also by keyword
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: None = None,
                        *,
                        platform_numbers: Iterable[str | int],
                        direction_id: int | None = None,
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

    # platform_numbers is specified by position, gtfs by keyword
    @overload
    def list_departures(self: Self,
                        route_type: RouteType,
                        stop_id: str,
                        route_id: None,
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
        :param gtfs: Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is False)
        :param include_advertised_interchange: Whether to include stop interchange information in result (server default is False)
        :param date: If specified, show departures from the specified date and time (server default is current time). If 'look_backwards' is True, show departures that arrive at their terminating destinations prior to the specified date and time instead. Defaults to UTC if timezone not specified
        :param max_results: Return only this number of departures
        :param include_cancelled: Whether to include departures that are cancelled (server default is False)
        :param look_backwards: If set to True, departures that arrive at their terminating destinations prior to the date and time specified in 'date' are returned instead (server default is False)
        :param expand: Optional data to include in the response (server default is "None")
        :param include_geopath: Include the run's path geometry (server default is False)
        :return: The requested departure information and any associated stop, route, run, direction and disruption data
        """

        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        req = f"/v3/departures/route_type/{route_type}/stop/{stop_id}" + (f"/route/{route_id}" if route_id is not None else "")
        req = self.build_arg_string("platform_numbers", platform_numbers, "direction_id", direction_id, "gtfs", gtfs, "include_advertised_interchange", include_advertised_interchange, "date_utc", date.astimezone(timezone.utc).isoformat() if date is not None else None, "max_results", max_results, "include_cancelled", include_cancelled, "look_backwards", look_backwards, "expand", expand, "include_geopath", include_geopath, s=req)

        res = self.call(req)
        return DeparturesResponse(**res)

    @overload
    def list_disruptions(self: Self,
                         *,
                         route_types: Iterable[RouteType] | RouteType | None = None,
                         disruption_modes: Iterable[Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | None = None,
                         disruption_status: Literal["Current", "Planned"] | None = None
                         ):
        """
        Returns a list of all current and planned disruptions.

        :param route_types: If specified, list only disruptions for the specified travel modes
        :param disruption_modes: If specified, list only disruptions for the specified disruption modes
        :param disruption_status: If specified, list only disruptions with the specified status
        :return: A list of disruptions
        """
        ...

    @overload
    def list_disruptions(self: Self,
                         route_id: int | None = None,
                         stop_id: int | None = None,
                         *,
                         disruption_status: Literal["Current", "Planned"] | None = None
                         ):
        """
        Returns a list of all disruptions for the specified route and/or stop.

        :param route_id: If route identifier is specified, list only disruptions for the specified route. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param stop_id: If stop identifier is specified, list only disruptions for the specified stop. If both route_id and stop_id are specified, list only disruptions for the specified route and stop
        :param disruption_status: If specified, list only disruptions with the specified status
        :return: A list of disruptions
        """
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

        return ret

    def get_disruption(self: Self, disruption_id: int) -> Disruption:
        """
        Retrieves the details of the disruption with the specified disruption identifier

        :param disruption_id: Disruption identifier
        :return: The disruption with the specified identifier
        """

        res = self.call(f"/v3/disruptions/{disruption_id}")["disruption"]
        return Disruption(**res)

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
        :param touch_on: If specified, estimate the fare for the journey commencing at the specified touch on time
        :param touch_off: If specified, estimate the fare for the journey concluding at the specified touch off time
        :param is_free_fare_zone: Whether the journey is entirely within a free fare zone
        :param route_types: If specified, estimate the fare for the journey travelling through the specified fare zone(s)
        :return: Object containing the estimated fares
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
        req = self.build_arg_string("touch_on", touch_on.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_on is not None else None, "touch_off", touch_off.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if touch_off is not None else None, "is_free_fare_zone", is_free_fare_zone, "travelled_route_types", route_types, s=req)

        res = self.call(req)["FareEstimateResult"]
        return FareEstimate(**res)

    @overload
    def list_outlets(self: Self,
                     *,
                     max_results: int | None = None
                     ) -> list[Outlet]:
        """
        Returns a list of all myki ticket outlets.

        :param max_results: Maximum number of outlets to be returned (server default is 30)
        :return: A list of ticket outlets
        """
        ...

    @overload
    def list_outlets(self: Self,
                     latitude: float,
                     longitude: float,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ) -> list[Outlet]:
        """
        Returns a list of ticket outlets near the specified location.

        :param latitude: If specified together with longitude, return ticket outlets near the specified location only
        :param longitude: If specified together with latitude, return ticket outlets near the specified location only
        :param max_distance: Maximum radius from the specified location to search, in metres (server default is 300 metres)
        :param max_results: Maximum number of outlets to be returned (server default is 30)
        :return: A list of ticket outlets
        """
        ...

    def list_outlets(self: Self,
                     latitude: float | None = None,
                     longitude: float | None = None,
                     max_distance: float | None = None,
                     max_results: int | None = None
                     ) -> list[Outlet]:

        req = "/v3/outlets" + (f"/location/{latitude},{longitude}" if latitude is not None and longitude is not None else "")
        req = self.build_arg_string("max_distance", max_distance, "max_results", max_results, s=req)

        res = self.call(req)["outlets"]
        return [Outlet(**item) for item in res]

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
        """
        Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

        If the search term is numeric or has fewer than 3 characters, the API will only return routes.

        :param search_term: Term to search
        :param route_types: Return stops and routes with the specified travel mode type(s) only
        :param include_outlets: Whether to include ticket outlets in search result (server default is True)
        :param match_stop_by_suburb: Whether to include stops in the search result where their localities match the search term (server default is True)
        :param match_route_by_suburb: Whether to include routes in the search result where their localities match the search term (server default is True)
        :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is False)
        :return: All matching stops, routes and ticket outlets
        """
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
        """
        Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

        If the search term is numeric or has fewer than 3 characters, the API will only return routes.

        :param search_term: Term to search
        :param latitude: Latitude coordinate of the location to search
        :param longitude: Longitude coordinate of the location to search
        :param max_distance: Radius, from centre location (specified in latitude and longitude parameters), of area to search in, in metres (server default is 300 metres)
        :param include_outlets: Whether to include ticket outlets in search result (server default is True)
        :param match_stop_by_suburb: Whether to include stops in the search result where their localities match the search term (server default is True)
        :param match_route_by_suburb: Whether to include routes in the search result where their localities match the search term (server default is True)
        :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is False)
        :return: All matching stops, routes and ticket outlets
        """
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
        """
        Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

        If the search term is numeric or has fewer than 3 characters, the API will only return routes.

        :param search_term: Term to search
        :param route_types: Return stops and routes with the specified travel mode type(s) only
        :param latitude: Latitude coordinate of the location to search
        :param longitude: Longitude coordinate of the location to search
        :param max_distance: Radius, from centre location (specified in latitude and longitude parameters), of area to search in, in metres (server default is 300 metres)
        :param include_outlets: Whether to include ticket outlets in search result (server default is True)
        :param match_stop_by_suburb: Whether to include stops in the search result where their localities match the search term (server default is True)
        :param match_route_by_suburb: Whether to include routes in the search result where their localities match the search term (server default is True)
        :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is False)
        :return: All matching stops, routes and ticket outlets
        """
        ...

    def search(self: Self,
               search_term: str,
               route_types: Iterable[RouteType] | RouteType | None = None,
               latitude: float | None = None,
               longitude: float | None = None,
               max_distance: float | None = None,
               include_outlets: bool | None = None,
               match_stop_by_suburb: bool | None = None,
               match_route_by_suburb: bool | None = None,
               match_stop_by_gtfs_stop_id: bool | None = None
               ) -> SearchResult:

        req = f"/v3/search/{search_term}"
        req = self.build_arg_string("route_types", route_types, "latitude", latitude, "longitude", longitude, "max_distance", max_distance, "include_outlets", include_outlets, "match_stop_by_suburb", match_stop_by_suburb, "match_route_by_suburb", match_route_by_suburb, "match_stop_by_gtfs_stop_id", match_stop_by_gtfs_stop_id, s=req)

        res = self.call(req)
        return SearchResult(**res)
