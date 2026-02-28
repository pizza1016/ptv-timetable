from typing import Literal, TypedDict

type FareZoneType = int

type APIResponse = Error | DeparturesResponse | DirectionsResponse | DisruptionResponse | DisruptionsResponse | DisruptionModesResponse | OutletResponse | OutletGeolocationResponse | RouteResponse | RoutesResponse | RouteTypesResponse | RunsResponse | SearchResult | StoppingPattern | StopsOnRouteResponse | StopsByDistanceResponse | FareEstimateResponse


class Status(TypedDict):
    """Contains API status information."""

    version: str
    """API version string"""
    health: Literal[0, 1]
    """API health status; 0 indicates API is offline, 1 indicates API is online"""


class Error(TypedDict):
    """Contains API error information."""

    message: str
    """Error message"""
    status: Status
    """API status information"""


class PathGeometry(TypedDict):
    """Represents the physical geometry of the attached route or run."""

    direction_id: int
    """Identifier of the direction of travel represented by this geometry"""
    valid_from: str
    """Date geometry is valid from"""
    valid_to: str
    """Date geometry is valid to"""
    paths: list[str]
    """Strings of coordinate pairs that draws the path"""


class StopAccessibilityWheelchair(TypedDict):
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
    manouvering: bool | None
    """Whether there is enough space for mobility devices to board or alight a public transport vehicle; None if not applicable or information unavailable"""
    raised_platform: bool | None
    """Whether the platform at this stop is raised to the height of the vehicle's floor; None if not applicable or information unavailable"""
    ramp: bool | None
    """Whether there are ramps with a height to length ratio less than 1:14 at this stop; None if not applicable or information unavailable"""
    secondary_path: bool | None
    """Whether there is a path outside this stop perimeter or boundary connecting to this stop that is accessible; None if not applicable or information unavailable"""
    raised_platform_shelther: bool | None
    """Whether there is shelter near the raised platform; None if not applicable or information unavailable"""
    steep_ramp: bool | None
    """Whether there are ramps with a height to length ratio greater than 1:14 at this stop; None if not applicable or information unavailable"""


class StopAccessibility(TypedDict):
    """Accessibility information for the attached stop."""

    lighting: bool
    """Whether there is lighting at this stop"""
    platform_number: str | None
    """The platform number of the stop that the data in this instance applies to; 0 if it applies to the entire stop in general; None if not applicable"""
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
    wheelchair: StopAccessibilityWheelchair
    """Wheelchair accessibility information for this stop"""


class StopAmenityDetails(TypedDict):
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
    seat: Literal[""]
    """Appears to be deprecated/unused (always returns empty string)"""
    stairs: Literal[""]
    """Appears to be deprecated/unused (always returns empty string)"""
    baby_change_facility: Literal[""]
    """Appears to be deprecated/unused (always returns empty string)"""
    parkiteer: None
    """Appears to be deprecated/unused (always returns None). Whether there is a Parkiteer (Bicycle Network) bicycle storage facility at this stop"""
    replacement_bus_stop_loc: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Location of the replacement bus stop"""
    QTEM: None
    """Appears to be deprecated/unused (always returns None)"""
    bike_storage: None
    """Appears to be deprecated/unused (always returns None)"""
    PID: bool
    """Whether there are passenger information displays at this stop"""
    ATM: None
    """Appears to be deprecated/unused (always returns None). Whether there is an automated teller machine at this stop"""
    travellers_aid: bool | None
    """Whether Traveller's Aid facilities are available at this stop; None if not applicable"""
    premium_stop: None
    """Appears to be deprecated/unused (always returns None)"""
    PSOs: None
    """Appears to be deprecated/unused (always returns None). Whether Protective Services Officers patrol this stop; None if not applicable"""
    melb_bike_share: None
    """Defunct (scheme no longer exists). Whether there are Melbourne Bike Share bicycle rentals available at this stop; None if not applicable or information unavailable"""
    luggage_storage: None
    """Appears to be deprecated/unused (always returns None). Whether luggage storage services are available at this stop; None if not applicable or information unavailable"""
    luggage_check_in: None
    """Appears to be deprecated/unused (always returns None). Whether luggage check-in facilities are available at this stop; None if not applicable or information unavailable"""
    toilet: bool
    """Whether there is a public toilet at or near this stop"""
    taxi_rank: bool
    """Whether there is a taxi rank at or near this stop"""
    car_parking: str
    """Number of fee-free parking spaces at this stop; empty string if not applicable"""
    cctv: bool
    """Whether there are closed-circuit television cameras at this stop"""


class StopContact(TypedDict):
    """Operator contact details for the attached stop."""

    phone: str | None
    """Main phone number of stop"""
    lost_property: str | None
    """Phone number for lost property"""
    feedback: str | None
    """Phone number to provide feedback"""
    lost_property_contact_number: None
    """Appears to be deprecated/unused (always returns None)"""


class StopGps(TypedDict):
    """GPS coordinates for the attached stop."""

    latitude: float
    """Latitude coordinate of this stop's location"""
    longitude: float
    """Longitude coordinate of this stop's location"""


class StopLocation(TypedDict):
    """Location details for the attached stop."""

    postcode: int
    """Postcode of stop"""
    municipality: str
    """Municipality (local government area) of location"""
    municipality_id: int
    """Municipality identifier"""
    suburb: str
    """Name of one of the roads near this stop (usually the crossing road, or "at" road), or a nearby landmark"""
    primary_stop_name: str
    """Name of one of the roads near this stop (usually the crossing road, or "at" road), or a nearby landmark"""
    road_type_primary: str
    """Road name suffix for 'primary_stop_name'"""
    second_stop_name: str
    """Name of one of the roads near this stop (usually the road of travel, or "on" road); may be empty"""
    road_type_second: str
    """Road name suffix for 'second_stop_name'"""
    bay_nbr: int | Literal[0]
    """For bus interchanges, the bay number of the particular stop; ``0`` if not applicable"""
    gps: StopGps
    """Coordinates of this stop's location"""


class StopStaffing(TypedDict):
    """Staffing hours for the attached stop."""

    mon_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Monday morning staffing hours start time"""
    mon_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Monday morning staffing hours end time"""
    mon_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Monday evening staffing hours start time"""
    mon_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Monday evening staffing hours end time"""
    tue_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Tuesday morning staffing hours start time"""
    tue_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Tuesday morning staffing hours end time"""
    tue_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Tuesday evening staffing hours start time"""
    tue_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Tuesday evening staffing hours end time"""
    wed_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Wednesday morning staffing hours start time"""
    wed_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Wednesday morning staffing hours end time"""
    wed_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Wednesday evening staffing hours start time"""
    wed_pm_To: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Wednesday evening staffing hours end time"""
    thu_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Thursday morning staffing hours start time"""
    thu_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Thursday morning staffing hours end time"""
    thu_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Thursday evening staffing hours start time"""
    thu_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Thursday evening staffing hours end time"""
    fri_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Friday morning staffing hours start time"""
    fri_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Friday morning staffing hours end time"""
    fri_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Friday evening staffing hours start time"""
    fri_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Friday evening staffing hours end time"""
    sat_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Saturday morning staffing hours start time"""
    sat_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Saturday morning staffing hours end time"""
    sat_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Saturday evening staffing hours start time"""
    sat_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Saturday evening staffing hours end time"""
    sun_am_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Sunday morning staffing hours start time"""
    sun_am_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Sunday morning staffing hours end time"""
    sun_pm_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Sunday evening staffing hours start time"""
    sun_pm_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Sunday evening staffing hours end time"""
    ph_from: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Public holiday staffing hours start time"""
    ph_to: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Public holiday staffing hours end time"""
    ph_additional_text: Literal[""]
    """Appears to be deprecated/unused (always returns empty string). Additional details about staffing on public holidays"""


class StopTicket(TypedDict):
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
    """Whether a V/Line reservation is required to travel to or from this station or stop; value should not be used for modes other than V/Lin"""
    ticket_zones: list[FareZoneType]
    """Ticketing zone(s) this stop is in"""


class VehicleDescriptor(TypedDict):
    """Describes information about a vehicle on a run."""

    operator: str | Literal[""] | None
    """Transport operator responsible for the vehicle; ``None`` or ``""`` (empty string) if this information is unavailable"""
    id: str | Literal[""] | None
    """Vehicle identifier used by the operator; ``None`` if this information is unavailable"""
    low_floor: bool | None
    """Whether the vehicle allows for step-free access at designated stops; ``None`` if this information is unavailable"""
    air_conditioned: bool | None
    """Whether the vehicle is air-conditioned; ``None`` if this information is unavailable"""
    description: str | Literal[""] | None
    """Description of the vehicle make/model and configuration; ``None`` if this information is unavailable"""
    supplier: str
    """Source of vehicle information"""
    length: str | None
    """Length of the vehicle; ``None`` if this information is unavailable"""


class VehiclePosition(TypedDict):
    """Represents the position of the attached vehicle."""

    latitude: float | None
    """Latitude coordinate of the vehicle's position; ``None`` if this information is unavailable"""
    longitude: float | None
    """Longitude coordinate of the vehicle's position; ``None`` if this information is unavailable"""
    easting: float | None
    """Easting of the vehicle's position in the easting-northing system; ``None`` if this information is unavailable"""
    northing: float | None
    """Northing of the vehicle's position in the easting-northing system; ``None`` if this information is unavailable"""
    direction: str
    """Description of the direction of travel (e.g. "inbound", "outbound")"""
    bearing: float | None
    """Vehicle's current direction of travel in degrees clockwise from geographic north; ``None`` if this information is unavailable"""
    supplier: str
    """Source of vehicle information"""
    datetime_utc: str | None
    """Date and time at which this position information is current; ISO 8601 full format, UTC time zone"""
    expiry_time: str | None
    """Date and time at which this position information is no longer valid; ISO 8601 full format, UTC time zone"""


class RouteType(TypedDict):
    """Represents a transport mode."""

    route_type_name: str
    """Name of the transport mode"""
    route_type: int
    """Identifier of the transport mode for use in API requests"""


class RouteServiceStatus(TypedDict):
    """Service status information for a route."""

    description: str
    """Brief description of the service status"""
    timestamp: str
    """Timestamp at which the returned service status is valid; ISO 8601 full format, UTC time zone"""


class BaseRoute(TypedDict):
    """Represents a route on the network."""

    route_id: int
    """Identifier of this route"""
    route_type: int
    """Identifier of the travel mode of this route"""
    route_name: str
    """Name of this route; trim leading and/or trailing whitespace before use"""
    route_number: str
    """Public-facing route number of this route"""
    route_gtfs_id: str
    """Identifier for this route in the General Transit Feed Specification"""


class Route(BaseRoute):
    """Represents a route on the network."""

    geopath: list[PathGeometry] | None
    """Physical geometry of this route"""


class RouteWithStatus(Route):
    """Represents a route on the network."""

    route_service_status: RouteServiceStatus
    """Service status of the route"""


class ResultRoute(BaseRoute):
    """Represents a route on the network."""

    route_service_status: RouteServiceStatus
    """Service status of the route"""


class DisruptionRoute(BaseRoute):
    """Represents a route on the network."""

    direction: DisruptionDirection | None
    """Information about the direction affected by the disruption; ``None`` if direction information is not provided"""


class StopBasic(TypedDict):
    """Represents a particular transport stop."""

    stop_id: int
    """Identifier of this stop"""
    stop_name: str
    """Name of this stop"""


class DisruptionStop(StopBasic):
    """Represents a particular transport stop."""
    pass


class StopIntermediate1(StopBasic):
    """Represents a particular transport stop."""

    route_type: Literal[0, 1, 2, 3]
    """Identifier of the travel mode of this stop"""
    stop_landmark: str
    """Notable landmarks near this stop; ``""`` (empty string) if none"""


class StopIntermediate2(StopIntermediate1):
    """Represents a particular transport stop."""

    stop_suburb: str
    """Locality (suburb/town) this stop is in; trim leading and/or trailing whitespace before use"""
    stop_latitude: float
    """Latitude coordinate of the stop's location"""
    stop_longitude: float
    """Longitude coordinate of the stop's location"""
    stop_sequence: int
    """Sort key for this stop along a route or run that is the subject of the API call; if neither were provided, value is ``0``"""


class StopModel(StopIntermediate2):
    """Represents a particular transport stop."""

    stop_distance: float
    """If a location was specified in the API call, distance in metres between this stop and that location; otherwise, ``0.0``"""


class StoppingPatternStop(StopModel):
    """Represents a particular transport stop."""

    stop_ticket: StopTicket
    """Ticketing information for this stop"""


class InterchangeRoute(TypedDict):
    """Represents a route that is available to be interchanged with at a stop"""

    route_id: int
    """Route identifier"""
    advertised: bool
    """Whether this route should be shown to users as being interchangeable at this stop"""


class StopOnRoute(StopIntermediate2):
    """Represents a particular transport stop."""

    disruption_ids: list[int]
    """Current and/or future disruptions affecting this stop"""
    interchange: list[InterchangeRoute]
    """Routes available to interchange with from this stop"""
    stop_ticket: StopTicket
    """Ticketing information for this stop"""


class ResultStop(StopModel):
    """Represents a particular transport stop."""

    routes: list[ResultRoute]
    """List of routes serving this stop"""


class StopGeosearch(StopModel):
    """Represents a particular transport stop."""

    disruption_ids: list[int]
    """Current and/or future disruptions affecting this stop"""
    routes: list[Route]
    """List of routes serving this stop"""


class StopDetails(StopIntermediate1):
    """Represents a particular transport stop."""

    point_id: int
    """Identifier of this stop in the PTV static timetable dump"""
    operating_hours: str
    """Description of railway station opening hours"""
    mode_id: int
    """Purpose unclear"""
    station_details_id: Literal[0]
    """Appears to be deprecated/unused (always returns ``0``)"""
    flexible_stop_opening_hours: Literal[""]
    """Appears to be deprecated/unused (always returns empty string)"""
    stop_contact: StopContact | None
    """Operator contact information for this stop; ``None`` if not requested from API"""
    stop_location: StopLocation | None
    """Location information about this stop; ``None`` if not requested from API"""
    stop_amenities: StopAmenityDetails | None
    """Facilities available at this stop; ``None`` if not requested from API"""
    stop_accessibility: StopAccessibility | None
    """Information about accessibility features available at this stop; ``None`` if not requested from API"""
    stop_staffing: StopStaffing | None
    """Appears to be deprecated/unused (fields always return empty strings)
    
    Staffing information for this stop; ``None`` if not requested from API
    """
    stop_ticket: StopTicket | None
    """Ticketing information for this stop; ``None`` if not requested from API"""
    station_type: Literal["Premium Station", "Host Station", "Unstaffed Station"] | None
    """Type of metropolitan train station: a premium station is staffed from first to last train and a host station is staffed only in the morning peak; ``None`` for other modes"""
    station_description: str | None
    """Additional information about this stop"""


class Departure(TypedDict):
    """Represents a specific departure from a specific stop."""

    stop_id: int
    """Identifier of departing stop"""
    route_id: int
    """Identifier of route of service"""
    direction_id: int
    """Travel direction identifier"""
    run_ref: str
    """Run/service identifier"""
    run_id: int | Literal[-1]
    """Run/service identifier; deprecated, use :attr:`run_ref` instead"""
    disruption_ids: list[int]
    """List of identifiers of disruptions affecting this stop and/or service"""
    scheduled_departure_utc: str
    """Departure time of service as timetabled; ISO 8601 full format, UTC time zone"""
    estimated_departure_utc: str | None
    """Estimated real-time departure time; ISO 8601 full format, UTC time zone; ``None`` if real-time departure time is unavailable"""
    at_platform: bool
    """Whether the train servicing this run is stopped at the platform"""
    platform_number: str
    """Expected platform number the train will depart from; this may change at any time prior to arriving at the stop"""
    flags: str
    """Unclear; appears to be some sort of run code"""
    departure_sequence: int
    """Sort key for this stop in a sequence of stops for this run"""
    departure_note: str
    """Notes about this departure (appears to be used to indicate whether a metropolitan train service runs via the City Loop or not)"""


class PatternDeparture(Departure):
    """Represents a specific departure from a specific stop."""

    skipped_stops: list[StopModel]
    """After departing from this stop, a sequence of stops that are skipped prior to arriving at the next departure point"""


class BaseRun(TypedDict):
    """Represents a particular run or service along a route."""

    run_ref: str
    """Identifier of this run"""
    route_id: int
    """Identifier of the route this run belongs to"""
    direction_id: int
    """Identifier of the direction of travel of this run"""
    destination_name: str | None
    """Public-facing destination name of this run"""


class InterchangeRun(BaseRun):
    """Represents a particular run or service along a route."""

    stop_id: int
    """Identifier of the stop where the original run (which contains this RunInterchange instance in its interchange field) changes over to this run, or vice versa"""
    advertised: bool
    """Whether the service swap is intended to be shown to passengers on public-facing displays"""


class Interchange(TypedDict):
    """Contains information about the preceding and/or subsequent service of a particular run."""

    feeder: InterchangeRun | None
    """The run this service was operating before it commenced, if any"""
    distributor: InterchangeRun | None
    """The run this service will operate after terminating, if any"""


class Run(BaseRun):
    """Represents a particular run or service along a route."""

    run_id: int | Literal[-1]
    """Identifier of this run; deprecated, use :attr:`run_ref` instead"""
    route_type: int
    """Identifier of the travel mode of this run"""
    final_stop_id: int
    """Identifier of the terminating stop of this run"""
    status: Literal["scheduled", "updated"]
    """Status of this metropolitan train service; always returns ``"scheduled"`` for all other modes"""
    run_sequence: int
    """Sort key for this run in a chronological list of runs for this route and direction of travel"""
    express_stop_count: int
    """Number of skipped stops in this run"""
    vehicle_position: VehiclePosition | None
    """Real-time vehicle position information where available; ``None`` if not requested from API"""
    vehicle_descriptor: VehicleDescriptor | None
    """Information on the vehicle operating this service, where available; ``None`` if not requested from API"""
    geopath: list[PathGeometry]
    """Physical geometry of this run's journey; ``[]`` (empty list) if not requested from API"""
    interchange: Interchange | None
    """Indicates, if any, the run this service was operating before it commenced ("feeder"), and the run this service will operate after terminating ("distributor"); ``None`` if no information available"""
    run_note: str
    """Notes about this run"""
    externalService: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    """Purpose unclear"""


class BaseDirection(TypedDict):
    """Represents a direction of travel on a particular route."""

    direction_id: int
    """Identifier for direction of travel"""
    direction_name: str
    """Name of direction of travel"""


class Direction(BaseDirection):
    """Represents a direction of travel on a particular route."""

    route_id: int
    """Identifier for the route specified by this direction of travel"""
    route_type: int
    """Identifier for the mode of travel of this route and destination"""


class DirectionWithDescription(Direction):
    """Represents a direction of travel on a particular route."""

    route_direction_description: str
    """Detailed description of this direction of travel along this route, as publicly displayed on the PTV website"""


class DisruptionDirection(BaseDirection):
    """Represents a direction of travel on a particular route."""

    route_direction_id: int
    """Combined identifier for the route and travel direction affected by the disruption"""
    service_time: str | None
    """Time of the run/service affected by the disruption; `""` (empty string) if disruption affects multiple or no runs/services"""


class Disruption(TypedDict):
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
    published_on: str
    """Date and time this disruption was published; ISO 8601 full format, UTC time zone"""
    last_updated: str
    """Date and time information about this disruption was last updated; ISO 8601 full format, UTC time zone"""
    from_date: str
    """Date and time this disruption began/will begin; ISO 8601 full format, UTC time zone"""
    to_date: str | None
    """Date and time this disruption will end; ISO 8601 full format, UTC time zone; ``None`` if unknown or uncertain"""
    routes: list[DisruptionRoute]
    """Routes affected by this disruption"""
    stops: list[DisruptionStop]
    """Stops affected by this disruption"""
    colour: str
    """Hex code for the alert colour on the disruption website"""
    display_on_board: bool
    """Indicates if this disruption is displayed on the PTV disruption boards across the network"""
    display_status: bool
    """Indicates if this disruption updates the service status of the affected routes on the disruption boards (presumably)"""


class Disruptions(TypedDict):
    """Disruptions relevant to the API request, categorised by the disruption mode."""

    general: list[Disruption]
    """Disruptions affecting public transport generally"""
    metro_train: list[Disruption]
    """Disruptions affecting metropolitan trains"""
    metro_tram: list[Disruption]
    """Disruptions affecting metropolitan trams"""
    metro_bus: list[Disruption]
    """Disruptions affecting metropolitan buses"""
    regional_train: list[Disruption]
    """Disruptions affecting regional trains"""
    regional_coach: list[Disruption]
    """Disruptions affecting regional coaches"""
    regional_bus: list[Disruption]
    """Disruptions affecting regional buses"""
    school_bus: list[Disruption]
    """Disruptions affecting school buses; not typically used"""
    telebus: list[Disruption]
    """Disruptions affecting telebuses; deprecated as telebuses no longer exist"""
    night_bus: list[Disruption]
    """Disruptions affecting night buses; deprecated as night buses are no longer a separate mode of travel and have been combined into :attr:`metro_bus`"""
    ferry: list[Disruption]
    """Disruptions affecting ferries; not typically used"""
    interstate_train: list[Disruption]
    """Disruptions affecting interstate trains; not typically used"""
    skybus: list[Disruption]
    """Disruptions affecting the Skybus network; not typically used"""
    taxi: list[Disruption]
    """Disruptions affecting taxis; not typically used"""


class DisruptionMode(TypedDict):
    """Represents a disruption mode."""

    disruption_mode_name: str
    """Name of the disruption mode"""
    disruption_mode: int
    """Identifier of the disruption mode for use in API requests"""


class Outlet(TypedDict):
    """Represents a ticket outlet."""

    outlet_slid_spid: str
    """Outlet SLID/SPID (beats me as to what that means, but it's some sort of identifier); PTV hubs return an empty string"""
    outlet_business: str
    """Name of the business"""
    outlet_latitude: float
    """Latitude coordinate of the outlet's position"""
    outlet_longitude: float
    """Longitude coordinate of the outlet's position"""
    outlet_name: str
    """Street address of the outlet"""
    outlet_suburb: str
    """Locality/suburb/town of the outlet"""
    outlet_postcode: int
    """Postcode of the outlet"""
    outlet_business_hour_mon: str | None
    """Outlet's business hours on Mondays"""
    outlet_business_hour_tue: str | None
    """Outlet's business hours on Tuesdays"""
    outlet_business_hour_wed: str | None
    """Outlet's business hours on Wednesdays"""
    outlet_business_hour_thur: str | None
    """Outlet's business hours on Thursdays"""
    outlet_business_hour_fri: str | None
    """Outlet's business hours on Fridays"""
    outlet_business_hour_sat: str | None
    """Outlet's business hours on Saturdays"""
    outlet_business_hour_sun: str | None
    """Outlet's business hours on Sundays"""
    outlet_notes: str | Literal[""] | None
    """Additional notes about the ticket outlet"""


class OutletGeolocation(Outlet):
    """Represents a ticket outlet."""

    outlet_distance: float
    """Distance of the outlet from the specified location"""


class ResultOutlet(Outlet):
    """Represents a ticket outlet."""

    outlet_distance: float
    """Distance of the outlet from the search location (for API search operations); ``0`` if no location was provided"""


class DeparturesResponse(TypedDict):
    """Response from the departures API (:meth: `ptv_timetable.TimetableAPI.list_departures`); also contains any relevant route, service and stop details."""

    departures: list[Departure]
    """Departures returned from the API request"""
    stops: dict[int, StopModel]
    """Mapping of stop identifiers to stop objects related to the returned departures; ``{}`` (empty dict) if not requested"""
    routes: dict[int, Route]
    """Mapping of route identifiers to route objects related to the returned departures; ``{}`` (empty dict) if not requested"""
    runs: dict[str, Run]
    """Mapping of run identifiers to run objects related to the returned departures; ``{}`` (empty dict) if not requested"""
    directions: dict[int, Direction]
    """Mapping of direction identifiers to direction objects related to the returned departures; ``{}`` (empty dict) if not requested"""
    disruptions: dict[int, Disruption]
    """Mapping of disruption identifiers to disruption objects related to the returned departures; ``{}`` (empty dict) if not requested"""
    status: Status
    """API status information"""


class DirectionsResponse(TypedDict):
    """Response from the directions API (:meth:`ptv_timetable.TimetableAPI.get_direction` and :meth:`ptv_timetable.TimetableAPI.list_route_directions`)."""

    directions: list[DirectionWithDescription]
    """Directions relevant to the API request"""
    status: Status
    """API status information"""


class DisruptionResponse(TypedDict):
    """Response from the disruption API."""

    disruption: Disruption | None
    """Disruption relevant to the API request; ``None`` if no disruption was found with the specified identifier"""
    status: Status
    """API status information"""


class DisruptionsResponse(TypedDict):
    """Response from the disruptions API."""

    disruptions: Disruptions
    """Disruptions relevant to the API request, categorised by the disruption mode"""
    status: Status
    """API status information"""


class DisruptionModesResponse(TypedDict):
    """Response from the disruption modes API."""

    disruption_modes: list[DisruptionMode]
    """List of valid disruption modes and their identifiers"""
    status: Status
    """API status information"""


class OutletResponse(TypedDict):
    """Response from the outlets API."""

    outlets: list[Outlet]
    """Ticket outlets relevant to the API request"""
    status: Status
    """API status information"""


class OutletGeolocationResponse(TypedDict):
    """Response from the outlets API when a location is specified."""

    outlets: list[OutletGeolocation]
    """Ticket outlets relevant to the API request"""
    status: Status
    """API status information"""


class RouteResponse(TypedDict):
    """Response from the route API."""

    route: RouteWithStatus | None
    """Route relevant to the API request; ``None`` if no route was found with the specified identifier"""
    status: Status
    """API status information"""


class RoutesResponse(TypedDict):
    """Response from the routes API."""

    routes: list[RouteWithStatus]
    """Routes relevant to the API request"""
    status: Status
    """API status information"""


class RouteTypesResponse(TypedDict):
    """Response from the route types API."""

    route_types: list[RouteType]
    """List of valid route types (transport mode) and their identifiers"""
    status: Status
    """API status information"""


class RunsResponse(TypedDict):
    """Response from the runs API."""

    runs: list[Run]
    """Runs relevant to the API request"""
    status: Status
    """API status information"""


class SearchResult(TypedDict):
    """Response from an API search request."""

    stops: list[ResultStop]
    """Stops matching the search parameters"""
    routes: list[ResultRoute]
    """Routes matching the search parameters"""
    outlets: list[ResultOutlet]
    """Outlets matching the search parameters, if requested; ``[]`` (empty list) otherwise"""
    status: Status
    """API status information"""


class StoppingPattern(TypedDict):
    """Represents a stopping pattern for a particular run. Sequence specified in departures field."""

    disruptions: list[Disruption]
    """List of disruptions affecting this run or the relevant routes and stops"""
    departures: list[PatternDeparture]
    """Sequence of departures from stops made by this run"""
    stops: dict[int, StoppingPatternStop]
    """Mapping of the relevant stop identifiers to :class:`StoppingPatternStop` objects"""
    routes: dict[int, Route]
    """Mapping of the relevant route identifiers to :class:`Route` objects"""
    runs: dict[str, Run]
    """Mapping of the relevant run identifiers to :class:`Run` objects"""
    directions: dict[int, Direction]
    """Mapping of the relevant travel direction identifiers to :class:`Direction` objects"""
    status: Status
    """API status information"""


class StopResponse(TypedDict):
    """Response from the stop API."""

    stop: StopDetails
    """Stop relevant to the API request (API raises an error if stop is not found)"""
    disruptions: dict[int, Disruption]
    """Any disruptions affecting the requested stop"""
    status: Status
    """API status information"""


class StopsOnRouteResponse(TypedDict):
    """Response from the stops API."""

    stops: list[StopOnRoute]
    """Stops relevant to the API request"""
    disruptions: dict[int, Disruption]
    """Any disruptions affecting the requested stops"""
    geopath: list[PathGeometry]
    """Path geometry of the route specified in the request"""
    status: Status
    """API status information"""


class StopsByDistanceResponse(TypedDict):
    """Response from the stops API."""

    stops: list[StopGeosearch]
    """Stops relevant to the API request"""
    disruptions: dict[int, Disruption]
    """Any disruptions affecting the requested stops"""
    status: Status
    """API status information"""


class ZoneInfo(TypedDict):
    """Contains information about the fare zones in a fare estimate API request."""

    MinZone: FareZoneType
    """Lowest zone in the journey"""
    MaxZone: FareZoneType
    """Highest zone in the journey"""
    UniqueZones: list[FareZoneType]
    """List of fare zones in the journey"""


class PassengerFare(TypedDict):
    """Contains the fare information for a specific ticket type."""

    PassengerType: Literal["fullFare", "concession", "senior"]
    """Ticket type for which the fares in this object apply to"""
    Fare2HourPeak: float
    """
    Fare for 2 hours of travel at any time of day.

    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.

    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    Fare2HourOffPeak: float
    """
    Fare for 2 hours of travel if tap on occurs outside designated peak periods.

    Time limit extends to 2.5 hours if travelling across 3-5 zones, 3 hours for 6-8 zones, 3.5 hours for 9-11 zones, 4 hours for 12-14 zones and 4.5 hours for 15 zones.

    For first tap-ons after 6 pm, the 2-hour fare is valid until 3 am the next morning.
    """
    FareDailyPeak: float
    """Daily cap for travel across the network at any time of day on weekdays"""
    FareDailyOffPeak: float
    """Daily cap for travel across the network on weekdays if tap on occurs entirely outside designated peak periods"""
    Pass7Days: float
    """Fare for unlimited travel for one week (total cost)"""
    Pass28To69DayPerDay: float
    """Fare, per day, for unlimited travel for 28 to 69 days"""
    Pass70PlusDayPerDay: float
    """Fare, per day, for unlimited travel for 70 to 325 days; passes for 326 to 365 days cost the same total amount as a 325-day pass"""
    WeekendCap: float
    """Daily cap for travel across the network on weekends"""
    HolidayCap: float
    """Daily cap for travel across the network on statutory public holidays"""


class FareEstimateResult(TypedDict):
    """Fare estimate for the specified travel returned by :meth:`ptv_timetable.TimetableAPI.getFareEstimate`. All fares in AUD."""

    IsEarlyBird: bool
    """Whether the touch on and off are made at metropolitan train stations on a non-public-holiday weekday before 7:15 am Melbourne time"""
    IsJourneyInFreeTramZone: bool
    """Whether this journey is entirely within a free fare zone"""
    IsThisWeekendJourney: bool
    """Whether this journey is made on a weekend or public holiday"""
    ZoneInfo: ZoneInfo
    """Information about the fare zones in the request"""
    PassengerFares: list[PassengerFare]
    """Fare information by ticket type"""


class FareEstimateResultStatus(TypedDict):
    """Status of the fare estimate API request."""

    Message: Literal["success", "non-myki route"]
    """Whether the API request was successful; otherwise, the reason for the failure"""
    StatusCode: Literal[0, 1]
    """``0`` if the request was successful, ``1`` if the request was unsuccessful"""


class FareEstimateResponse(TypedDict):
    """Response from the fare estimate API."""

    FareEstimateResult: FareEstimateResult
    """Estimated fares for the requested journey; ``None`` if the estimated fares couldn't be obtained"""
    FareEstimateResultStatus: FareEstimateResultStatus
    """Status of the API request"""
