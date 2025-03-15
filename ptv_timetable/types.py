from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from dataclasses import asdict, astuple, dataclass
from datetime import datetime
from typing import Any, Final, final, Literal, overload, override, Self, TypedDict
from zoneinfo import ZoneInfo
import enum
import platform
import re
if platform.system() == "Windows":
    import tzdata

__all__ = ["TZ_MELBOURNE", "UUID_PATTERN", "METROPOLITAN_TRAIN", "METRO_TRAIN", "MET_TRAIN", "METRO", "TRAM", "BUS", "REGIONAL_TRAIN", "REG_TRAIN", "COACH", "VLINE", "EXPAND_ALL", "EXPAND_STOP", "EXPAND_ROUTE", "EXPAND_RUN", "EXPAND_DIRECTION", "EXPAND_DISRUPTION", "EXPAND_VEHICLE_DESCRIPTOR", "EXPAND_VEHICLE_POSITION", "EXPAND_NONE", "NOT_PROVIDED", "TimetableData", "PathGeometry", "StopTicket", "StopContact", "StopLocation", "StopAmenities", "Wheelchair", "StopAccessibility", "StopStaffing", "Route", "Stop", "Departure", "VehiclePosition", "VehicleDescriptor", "Run", "Direction", "Disruption", "StoppingPattern", "DeparturesResponse", "Outlet", "FareEstimate", "SearchResult"]

TZ_MELBOURNE: Final = ZoneInfo("Australia/Melbourne")
"""Time zone of Victoria"""
UUID_PATTERN: Final = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")
"""Regular expression for a universally unique identifier"""

METROPOLITAN_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in ``route_type`` parameters"""
METRO_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in ``route_type`` parameters"""
MET_TRAIN: Literal[0] = 0
"""Metropolitan trains. For use in ``route_type`` parameters"""
METRO: Literal[0] = 0
"""Metropolitan trains. For use in ``route_type`` parameters"""
TRAM: Literal[1] = 1
"""Metropolitan trams. For use in ``route_type`` parameters"""
BUS: Literal[2] = 2
"""Metropolitan & regional buses. For use in ``route_type`` parameters"""
REGIONAL_TRAIN: Literal[3] = 3
"""Regional trains & coaches. For use in ``route_type`` parameters"""
REG_TRAIN: Literal[3] = 3
"""Regional trains & coaches. For use in ``route_type`` parameters"""
COACH: Literal[3] = 3
"""Regional trains & coaches. For use in ``route_type`` parameters"""
VLINE: Literal[3] = 3
"""Regional trains & coaches. For use in ``route_type`` parameters"""

EXPAND_ALL: Literal["All"] = "All"
"""Return all object properties in full. For use in ``expand`` parameters"""
EXPAND_STOP: Literal["Stop"] = "Stop"
"""Return stop properties. For use in ``expand`` parameters"""
EXPAND_ROUTE: Literal["Route"] = "Route"
"""Return route properties. For use in ``expand`` parameters"""
EXPAND_RUN: Literal["Run"] = "Run"
"""Return run properties. For use in ``expand`` parameters"""
EXPAND_DIRECTION: Literal["Direction"] = "Direction"
"""Return direction properties. For use in ``expand`` parameters"""
EXPAND_DISRUPTION: Literal["Disruption"] = "Disruption"
"""Return disruption properties. For use in ``expand`` parameters"""
EXPAND_VEHICLE_DESCRIPTOR: Literal["VehicleDescriptor"] = "VehicleDescriptor"
"""Return vehicle descriptor properties. For use in ``expand`` parameters"""
EXPAND_VEHICLE_POSITION: Literal["VehiclePosition"] = "VehiclePosition"
"""Return vehicle position properties. For use in ``expand`` parameters"""
EXPAND_NONE: Literal["None"] = "None"
"""Don't return any object properties. For use in ``expand`` parameters"""

@final
@enum.unique
class _NotProvidedType(enum.Enum):
    """Type of the :const:`NOT_PROVIDED` constant.

    .. versionadded:: 0.3.0
    """

    NOT_PROVIDED = enum.auto()
    """Sentinel value that indicates that the API operation used does not return the information in this field"""

    def __bool__(self: Self) -> bool:
        if self is self.NOT_PROVIDED:
            return False
        raise TypeError(f"expected _NotProvidedType, got {type(self).__name__}")

    def __repr__(self: Self) -> str:
        if self is self.NOT_PROVIDED:
            return "_NotProvidedType.NOT_PROVIDED"
        raise TypeError(f"expected _NotProvidedType, got {type(self).__name__}")


    def __str__(self: Self) -> str:
        if self is self.NOT_PROVIDED:
            return "NOT_PROVIDED"
        raise TypeError(f"expected _NotProvidedType, got {type(self).__name__}")

NOT_PROVIDED: Final = _NotProvidedType.NOT_PROVIDED
"""Sentinel value that indicates that the API operation used does not return the information in this field

.. versionadded:: 0.3.0
"""

@dataclass(kw_only=True, slots=True)
class TimetableData(object, metaclass=ABCMeta):
    """Base class for API response types."""

    @overload
    def as_dict(self: Self, *, dict_factory: None = None) -> dict[str, Any]:
        ...

    @overload
    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, Any]]], _T]) -> _T:
        ...

    def as_dict[_T](self: Self, *, dict_factory: Callable[[list[tuple[str, Any]]], _T] | None = None) -> _T | dict[str, Any]:
        """Converts this :class:`TimetableData` dataclass instance to a :class:`dict` that maps its field names to their corresponding values, recursing into any dataclasses, dicts, lists and tuples and doing a :func:`~copy.deepcopy` of everything else. The result can be customised by providing a ``dict_factory`` function.

        This is a convenient shorthand for :func:`dataclasses.asdict(self) <dataclasses.asdict>`.

        :param dict_factory: If specified, dict creation will be customised with this function (including for nested dataclasses)
        :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``

        .. versionadded:: 0.2.0
        """
        return asdict(self) if dict_factory is None else asdict(self, dict_factory=dict_factory)

    @overload
    def as_tuple(self: Self, *, tuple_factory: None = None) -> tuple[Any, ...]:
        ...

    @overload
    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T]) -> _T:
        ...

    def as_tuple[_T](self: Self, *, tuple_factory: Callable[[list[Any]], _T] | None = None) -> tuple[Any, ...] | _T:
        """Converts this :class:`TimetableData` dataclass instance to a :class:`tuple` of its fields' values, recursing into any dataclasses, dicts, lists and tuples and doing a :func:`~copy.deepcopy` of everything else. The result can be customised by providing a ``tuple_factory`` function.

        This is a convenient shorthand for :func:`dataclasses.astuple(self) <dataclasses.astuple>`.

        :param tuple_factory: If specified, tuple creation will be customised with this function (including for nested dataclasses)
        :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``

        .. versionadded:: 0.2.0
        """
        return astuple(self) if tuple_factory is None else astuple(self, tuple_factory=tuple_factory)

    @classmethod
    @abstractmethod
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        """Constructs a new instance of this class by converting the specified API response data.

        :param kwargs: A dictionary unpacking with the data to instantiate
        :return:       The newly constructed instance
        """
        ...

    @classmethod
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        """Asynchronously constructs a new instance of this class by converting the specified API response data.

        :param kwargs: A dictionary unpacking with the data to instantiate
        :return:       The newly constructed instance

        .. versionadded:: 0.4.0
        """
        return cls.load(**kwargs)


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
    """Appears to be deprecated/unused (always returns None). Whether there is a Parkiteer (Bicycle Network) bicycle storage facility at this stop"""
    replacement_bus_stop_location: str
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

    platform_number: str | None
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
    geometry: list[PathGeometry] | None | _NotProvidedType = NOT_PROVIDED
    """Physical geometry of this route"""
    route_service_status: TypedDict("RouteServiceStatus", {"description": str, "timestamp": datetime}) | _NotProvidedType = NOT_PROVIDED
    """Service status of the route; :const:`NOT_PROVIDED` if API did not provide this information
    
    .. versionchanged:: 0.3.0
        Changed attribute type from :class:`dict` to :class:`~typing.TypedDict`.
    """

    # From /v3/disruptions/...
    route_direction_id: int | None | _NotProvidedType = NOT_PROVIDED
    """For a disruption, combined identifier for the route and travel direction affected by the disruption; :const:`NOT_PROVIDED` if not applicable"""
    direction_id: int | None | _NotProvidedType = NOT_PROVIDED
    """For a disruption, identifier of travel direction affected by the disruption; :const:`NOT_PROVIDED` if not applicable"""
    direction_name: str | None | _NotProvidedType = NOT_PROVIDED
    """For a disruption, destination of travel direction affected by the disruption; :const:`NOT_PROVIDED` if not applicable"""
    service_time: str | None | _NotProvidedType = NOT_PROVIDED
    """For a disruption, time of the run/service affected by the disruption; :const:`NOT_PROVIDED` if not applicable, or disruption affects multiple or no runs/services"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        route_name = kwargs.pop("route_name").strip()
        if "geopath" in kwargs:
            geometry = [PathGeometry.load(**item) for item in kwargs.pop("geopath")]
        else:
            geometry = NOT_PROVIDED
        route_service_status = kwargs.pop("route_service_status") if "route_service_status" in kwargs else NOT_PROVIDED
        if route_service_status is not NOT_PROVIDED:
            route_service_status["timestamp"] = datetime.fromisoformat(route_service_status["timestamp"]).astimezone(TZ_MELBOURNE)
        if "direction" in kwargs:
            direction = kwargs.pop("direction")
            route_direction_id = direction["route_direction_id"]
            direction_id = direction["direction_id"]
            direction_name = direction["direction_name"]
            service_time = direction["service_time"]
        else:
            route_direction_id = direction_id = direction_name = service_time = NOT_PROVIDED
        return cls(route_name=route_name, geometry=geometry, route_service_status=route_service_status, route_direction_id=route_direction_id, direction_id=direction_id, direction_name=direction_name, service_time=service_time, **kwargs)

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        route_name = kwargs.pop("route_name").strip()
        if "geopath" in kwargs:
            geometry = [await PathGeometry.aload(**item) for item in kwargs.pop("geopath")]
        else:
            geometry = NOT_PROVIDED
        route_service_status = kwargs.pop("route_service_status") if "route_service_status" in kwargs else NOT_PROVIDED
        if route_service_status is not NOT_PROVIDED:
            route_service_status["timestamp"] = datetime.fromisoformat(route_service_status["timestamp"]).astimezone(TZ_MELBOURNE)
        if "direction" in kwargs:
            direction = kwargs.pop("direction")
            route_direction_id = direction["route_direction_id"]
            direction_id = direction["direction_id"]
            direction_name = direction["direction_name"]
            service_time = direction["service_time"]
        else:
            route_direction_id = direction_id = direction_name = service_time = NOT_PROVIDED
        return cls(route_name=route_name, geometry=geometry, route_service_status=route_service_status, route_direction_id=route_direction_id, direction_id=direction_id, direction_name=direction_name, service_time=service_time, **kwargs)


@dataclass(kw_only=True, slots=True)
class Stop(TimetableData):
    """Represents a particular transport stop."""

    stop_id: int
    """Identifier of this stop"""
    route_type: int | _NotProvidedType = NOT_PROVIDED
    """Identifier of the travel mode of this stop; :const:`NOT_PROVIDED` if this was created by 'Disruptions'"""
    stop_name: str
    """Name of this stop"""
    locality: str | _NotProvidedType = NOT_PROVIDED
    """Locality (suburb/town) this stop is in; :const:`NOT_PROVIDED` if the API response did not return this information"""
    stop_latitude: float | _NotProvidedType = NOT_PROVIDED
    """Latitude coordinate of the stop's location; :const:`NOT_PROVIDED` if the API response did not return this information"""
    stop_longitude: float | _NotProvidedType = NOT_PROVIDED
    """Longitude coordinate of the stop's location; :const:`NOT_PROVIDED` if the API response did not return this information"""
    stop_distance: float | _NotProvidedType = NOT_PROVIDED
    """If a location was specified in the API call, distance in metres between this stop and that location; otherwise, 0.0 or :const:`NOT_PROVIDED`"""
    stop_landmark: str | _NotProvidedType = NOT_PROVIDED
    """Notable landmarks near this stop; "" (empty string) if none; :const:`NOT_PROVIDED` if this was created by 'Disruptions'"""
    stop_sequence: int | _NotProvidedType = NOT_PROVIDED
    """Sort key for this stop along a route or run that is the subject of the API call; if neither were provided, value is 0"""
    stop_ticket: StopTicket | _NotProvidedType = NOT_PROVIDED
    """Ticketing information for this stop; :const:`NOT_PROVIDED` if the API response did not return this information"""
    interchange: list[TypedDict("StopInterchange", {"route_id": int, "advertised": bool})] | _NotProvidedType = NOT_PROVIDED
    """Routes available to interchange with from this stop; :const:`NOT_PROVIDED` if the API response did not return this information
    
    .. versionchanged:: 0.3.1
        Changed attribute type from :class:`dict` to :class:`~typing.TypedDict`.
    """

    # From /v3/stops/...
    point_id: int | _NotProvidedType = NOT_PROVIDED
    """Identifier of this stop in the PTV static timetable dump; :const:`NOT_PROVIDED` if the API operation doesn't use this field"""
    disruption_ids: list[int] | _NotProvidedType = NOT_PROVIDED
    """Current or future disruptions affecting this stop; :const:`NOT_PROVIDED` if the API operation doesn't use this field"""
    routes: list[Route] | _NotProvidedType = NOT_PROVIDED
    """List of routes serving this stop; :const:`NOT_PROVIDED` if the API operation doesn't use this field"""
    operating_hours: str | _NotProvidedType = NOT_PROVIDED
    """Description of railway station opening hours; :const:`NOT_PROVIDED` if the API operation doesn't use this field"""
    mode_id: int | _NotProvidedType = NOT_PROVIDED
    """Purpose unclear; appears to correspond to disruption modes, which is not currently implemented in this module as it duplicates the purpose of RouteType"""
    station_details_id: int | _NotProvidedType = NOT_PROVIDED
    """Appears to be deprecated/unused (always returns 0)"""
    flexible_stop_opening_hours: str | _NotProvidedType = NOT_PROVIDED
    """Appears to be deprecated/unused (always returns empty string)"""
    stop_contact: StopContact | _NotProvidedType = NOT_PROVIDED
    """Operator contact information for this stop; :const:`NOT_PROVIDED` if not requested from API"""
    stop_location: StopLocation | _NotProvidedType = NOT_PROVIDED
    """Location information about this stop; :const:`NOT_PROVIDED` if not requested from API"""
    stop_amenities: StopAmenities | _NotProvidedType = NOT_PROVIDED
    """Facilities available at this stop; :const:`NOT_PROVIDED` if not requested from API"""
    stop_accessibility: StopAccessibility | _NotProvidedType = NOT_PROVIDED
    """Information about accessibility features available at this stop; :const:`NOT_PROVIDED` if not requested from API"""
    stop_staffing: StopStaffing | _NotProvidedType = NOT_PROVIDED
    """Staffing information for this stop; :const:`NOT_PROVIDED` if not requested from API"""
    station_type: Literal["Premium Station", "Host Station", "Unstaffed Station"] | None | _NotProvidedType = NOT_PROVIDED
    """Type of metropolitan train station: a premium station is staffed from first to last train and a host station is staffed only in the morning peak; None for other modes; :const:`NOT_PROVIDED` if the API operation doesn't use this field"""
    station_description: str | _NotProvidedType = NOT_PROVIDED
    """Additional information about this stop"""

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        stop_name = kwargs.pop("stop_name").strip()
        locality = kwargs.pop("stop_suburb") if "stop_suburb" in kwargs else None
        stop_ticket = StopTicket.load(**kwargs.pop("stop_ticket")) if "stop_ticket" in kwargs and kwargs["stop_ticket"] is not None else kwargs.pop("stop_ticket", NOT_PROVIDED)
        routes = [Route.load(**item) for item in kwargs.pop("routes")] if "routes" in kwargs and kwargs["routes"] is not None else kwargs.pop("routes", NOT_PROVIDED)
        stop_contact = StopContact.load(**kwargs.pop("stop_contact")) if "stop_contact" in kwargs and kwargs["stop_contact"] is not None else kwargs.pop("stop_contact", NOT_PROVIDED)
        stop_location = StopLocation.load(**kwargs.pop("stop_location")) if "stop_location" in kwargs and kwargs["stop_location"] is not None else kwargs.pop("stop_location", NOT_PROVIDED)
        stop_amenities = StopAmenities.load(**kwargs.pop("stop_amenities")) if "stop_amenities" in kwargs and kwargs["stop_amenities"] is not None else kwargs.pop("stop_amenities", NOT_PROVIDED)
        stop_accessibility = StopAccessibility.load(**kwargs.pop("stop_accessibility")) if "stop_accessibility" in kwargs and kwargs["stop_accessibility"] is not None else kwargs.pop("stop_accessibility", NOT_PROVIDED)
        stop_staffing = StopStaffing.load(**kwargs.pop("stop_staffing")) if "stop_staffing" in kwargs and kwargs["stop_staffing"] is not None else kwargs.pop("stop_staffing", NOT_PROVIDED)
        return cls(stop_name=stop_name, locality=locality, stop_ticket=stop_ticket, routes=routes, stop_contact=stop_contact, stop_location=stop_location, stop_amenities=stop_amenities, stop_accessibility=stop_accessibility, stop_staffing=stop_staffing, **kwargs)

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        stop_name = kwargs.pop("stop_name").strip()
        locality = kwargs.pop("stop_suburb") if "stop_suburb" in kwargs else None
        stop_ticket = await StopTicket.aload(**kwargs.pop("stop_ticket")) if "stop_ticket" in kwargs and kwargs["stop_ticket"] is not None else kwargs.pop("stop_ticket", NOT_PROVIDED)
        routes = [await Route.aload(**item) for item in kwargs.pop("routes")] if "routes" in kwargs and kwargs["routes"] is not None else kwargs.pop("routes", NOT_PROVIDED)
        stop_contact = await StopContact.aload(**kwargs.pop("stop_contact")) if "stop_contact" in kwargs and kwargs["stop_contact"] is not None else kwargs.pop("stop_contact", NOT_PROVIDED)
        stop_location = await StopLocation.aload(**kwargs.pop("stop_location")) if "stop_location" in kwargs and kwargs["stop_location"] is not None else kwargs.pop("stop_location", NOT_PROVIDED)
        stop_amenities = await StopAmenities.aload(**kwargs.pop("stop_amenities")) if "stop_amenities" in kwargs and kwargs["stop_amenities"] is not None else kwargs.pop("stop_amenities", NOT_PROVIDED)
        stop_accessibility = await StopAccessibility.aload(**kwargs.pop("stop_accessibility")) if "stop_accessibility" in kwargs and kwargs["stop_accessibility"] is not None else kwargs.pop("stop_accessibility", NOT_PROVIDED)
        stop_staffing = await StopStaffing.aload(**kwargs.pop("stop_staffing")) if "stop_staffing" in kwargs and kwargs["stop_staffing"] is not None else kwargs.pop("stop_staffing", NOT_PROVIDED)
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
    """Expected platform number the train will depart from; this may change at any time up to prior to arriving at the stop
    
    .. versionchanged:: 0.3.1
        Changed attribute type from (the erroneous) :class:`int` to :class:`str`.
    """
    flags: str
    """Unclear; appears to be some sort of run code"""
    departure_sequence: int
    """Sort key for this stop in a sequence of stops for this run"""

    # From /v3/pattern/...
    skipped_stops: list[Stop] | _NotProvidedType = NOT_PROVIDED
    """After departing from this stop, a sequence of stops that are skipped prior to arriving at the next departure point"""

    # Undocumented
    departure_note: str | None
    """Notes about this departure (appears to be used to indicate whether a metropolitan train service runs via the City Loop or not)"""

    @property
    def departure_time(self: Self) -> datetime:
        """Returns `estimated_departure` if its value is not ``None``, otherwise returns `scheduled_departure`.

        :return: `estimated_departure` if not ``None``, else `scheduled_departure`

        .. versionadded:: 0.3.1
        """
        return self.estimated_departure if self.estimated_departure is not None else self.scheduled_departure

    @classmethod
    @override
    def load(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        scheduled_departure = datetime.fromisoformat(kwargs.pop("scheduled_departure_utc")).astimezone(TZ_MELBOURNE)
        estimated_departure = datetime.fromisoformat(kwargs.pop("estimated_departure_utc")).astimezone(TZ_MELBOURNE) if kwargs["estimated_departure_utc"] is not None else kwargs.pop("estimated_departure_utc")
        skipped_stops = [Stop.load(**item) for item in kwargs.pop("skipped_stops")] if "skipped_stops" in kwargs and kwargs["skipped_stops"] is not None else kwargs.pop("skipped_stops", None)
        kwargs.pop("run_id")
        return cls(scheduled_departure=scheduled_departure, estimated_departure=estimated_departure, skipped_stops=skipped_stops, **kwargs)

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        scheduled_departure = datetime.fromisoformat(kwargs.pop("scheduled_departure_utc")).astimezone(TZ_MELBOURNE)
        estimated_departure = datetime.fromisoformat(kwargs.pop("estimated_departure_utc")).astimezone(TZ_MELBOURNE) if kwargs["estimated_departure_utc"] is not None else kwargs.pop("estimated_departure_utc")
        skipped_stops = [await Stop.aload(**item) for item in kwargs.pop("skipped_stops")] if "skipped_stops" in kwargs and kwargs["skipped_stops"] is not None else kwargs.pop("skipped_stops", None)
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
class RunInterchange(TimetableData):
    """Contains information about the preceding or subsequent service of a particular run.

    .. versionadded:: 0.3.1
    """

    run_ref: str
    """Identifier of this run"""
    route_id: int
    """Identifier of the route this run belongs to"""
    direction_id: int
    """Identifier of the direction of travel of this run"""
    stop_id: int
    """Identifier of the stop where the original run (which contains this RunInterchange instance in its interchange field) changes over to this run, or vice versa"""
    destination_name: str
    """Public-facing destination name of this run"""
    advertised: bool
    """Whether the service swap is intended to be shown to passengers on public-facing signage"""

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
    interchange: dict[Literal["feeder", "distributor"], RunInterchange | None] | None
    """Indicates, if any, the run this service was operating before commencing ("feeder"), and the run this service will operate after terminating ("distributor"); None if no information available, or this information was not requested from the API"""

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

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        kwargs.pop("run_id")
        destination_name = kwargs.pop("destination_name")
        if destination_name is not None:
            destination_name = destination_name.strip()
        geometry = [await PathGeometry.aload(**item) for item in kwargs.pop("geopath")]
        vehicle_position = await VehiclePosition.aload(**kwargs.pop("vehicle_position")) if kwargs["vehicle_position"] is not None else kwargs.pop("vehicle_position")
        vehicle_descriptor = await VehicleDescriptor.aload(**kwargs.pop("vehicle_descriptor")) if kwargs["vehicle_descriptor"] is not None else kwargs.pop("vehicle_descriptor")
        return cls(destination_name=destination_name, geometry=geometry, vehicle_position=vehicle_position, vehicle_descriptor=vehicle_descriptor, **kwargs)


@dataclass(kw_only=True, slots=True)
class Direction(TimetableData):
    """Represents a direction of travel on a particular route."""

    direction_id: int
    """Identifier for direction of travel"""
    direction_name: str
    """Name of direction of travel"""
    route_direction_description: str | _NotProvidedType = NOT_PROVIDED
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

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        published_on = datetime.fromisoformat(kwargs.pop("published_on")).astimezone(TZ_MELBOURNE)
        last_updated = datetime.fromisoformat(kwargs.pop("last_updated")).astimezone(TZ_MELBOURNE)
        from_date = datetime.fromisoformat(kwargs.pop("from_date")).astimezone(TZ_MELBOURNE)
        to_date = datetime.fromisoformat(kwargs.pop("to_date")).astimezone(TZ_MELBOURNE) if kwargs["to_date"] is not None else kwargs.pop("to_date")
        routes = [await Route.aload(**item) for item in kwargs.pop("routes")]
        stops = [await Stop.aload(**item) for item in kwargs.pop("stops")]
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

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        disruptions = [await Disruption.aload(**item) for item in kwargs.pop("disruptions")]
        departures = [await Departure.aload(**item) for item in kwargs.pop("departures")]
        stops = {int(key): await Stop.aload(**value) for key, value in kwargs.pop("stops").items()}
        routes = {int(key): await Route.aload(**value) for key, value in kwargs.pop("routes").items()}
        runs = {key: await Run.aload(**value) for key, value in kwargs.pop("runs").items()}
        directions = {int(key): await Direction.aload(**value) for key, value in kwargs.pop("directions").items()}
        return cls(disruptions=disruptions, departures=departures, stops=stops, routes=routes, runs=runs, directions=directions)

    def simple(self: Self) -> list[int]:
        """
        Returns the stopping pattern as a simple sequence of stop identifiers.

        :return: A list of stop identifiers.

        .. versionadded:: 0.2.0
        """
        return [departure.stop_id for departure in self.departures]


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

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        departures = [await Departure.aload(**item) for item in kwargs.pop("departures")]
        stops = {int(key): await Stop.aload(**value) for key, value in kwargs.pop("stops").items()}
        routes = {int(key): await Route.aload(**value) for key, value in kwargs.pop("routes").items()}
        runs = {key: await Run.aload(**value) for key, value in kwargs.pop("runs").items()}
        directions = {int(key): await Direction.aload(**value) for key, value in kwargs.pop("directions").items()}
        disruptions = {int(key): await Disruption.aload(**value) for key, value in kwargs.pop("disruptions").items()}
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
    outlet_distance: float | _NotProvidedType = NOT_PROVIDED
    """Distance of the outlet from the search location (for API search operations); 0 if no location is provided, :const:`NOT_PROVIDED` if the operation doesn't use this field"""

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

        return cls(early_bird_travel=early_bird_travel, free_fare_zone=free_fare_zone, weekend=weekend, zones=zones, full_2_hour_peak=full_2_hour_peak, full_2_hour_off_peak=full_2_hour_off_peak, full_weekday_cap_peak=full_weekday_cap_peak, full_weekday_cap_off_peak=full_weekday_cap_off_peak, full_weekend_cap=full_weekend_cap, full_holiday_cap=full_holiday_cap, full_pass_7_days_total=full_pass_7_days_total, full_pass_28_to_69_days=full_pass_28_to_69_days, full_pass_70_plus_days=full_pass_70_plus_days, concession_2_hour_peak=concession_2_hour_peak, concession_2_hour_off_peak=concession_2_hour_off_peak, concession_weekday_cap_peak=concession_weekday_cap_peak, concession_weekday_cap_off_peak=concession_weekday_cap_off_peak, concession_weekend_cap=concession_weekend_cap, concession_holiday_cap=concession_holiday_cap, concession_pass_7_days_total=concession_pass_7_days_total, concession_pass_28_to_69_days=concession_pass_28_to_69_days, concession_pass_70_plus_days=concession_pass_70_plus_days, senior_2_hour_peak=senior_2_hour_peak, senior_2_hour_off_peak=senior_2_hour_off_peak, senior_weekday_cap_peak=senior_weekday_cap_peak, senior_weekday_cap_off_peak=senior_weekday_cap_off_peak, senior_weekend_cap=senior_weekend_cap, senior_holiday_cap=senior_holiday_cap, senior_pass_7_days_total=senior_pass_7_days_total, senior_pass_28_to_69_days=senior_pass_28_to_69_days, senior_pass_70_plus_days=senior_pass_70_plus_days)


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

    @classmethod
    @override
    async def aload(cls: Self, **kwargs: str | int | float | bool | list | dict | None) -> Self:
        stops = [await Stop.aload(**item) for item in kwargs.pop("stops")]
        routes = [await Route.aload(**item) for item in kwargs.pop("routes")]
        outlets = [await Outlet.aload(**item) for item in kwargs.pop("outlets")]
        kwargs.pop("status")
        return cls(stops=stops, routes=routes, outlets=outlets)
