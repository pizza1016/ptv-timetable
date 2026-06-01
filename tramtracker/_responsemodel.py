from typing import TypedDict, Literal


type TramTrackerResponse = DestinationsResponse | StopResponse | StopsResponse | RoutesResponse | DeparturesResponse | ColourResponse
"""Union of all possible response objects"""


class Destination(TypedDict):
    """Represents a destination of a tram route."""

    RouteNo: int
    """Public-facing route number for this destination"""
    InternalRouteNo: int
    """Route identifier for this destination"""
    AlphaNumericRouteNo: str | None
    """Public-facing route number for this destination (if it contains letters)"""
    Destination: str
    """Name of this destination"""
    IsUpDestination: bool
    """Whether this destination is in the "up" direction"""
    HasLowFloor: bool
    """Whether low-floor trams service this route (either fully or partially)"""


class DestinationsResponse(TypedDict):
    """Raw response type of ``/GetAllRoutes.ashx``"""

    ResponseObject: list[Destination]
    """The response data"""
    ResponseString: str | None
    """Error message, if any"""
    HasError: bool
    """Whether the server reported an error"""


class Stop1(TypedDict):
    """Represents a tram stop."""

    StopID: None
    """Currently unused"""
    Description: str
    """Name of this stop"""
    StopName: str
    """Number and name of this stop"""
    StopNo: int
    """This stop's TramTracker code"""
    DistanceToLocation: float
    """Currently unused"""
    Destination: None
    """Currently unused"""
    Suburb: str
    """Locality (suburb/town) this stop is in; ``None`` if not provided"""
    Latitude: float
    """Currently unused; will always return ``0.0``"""
    Longitude: float
    """Currently unused; will always return ``0.0``"""
    RouteNo: Literal[0]
    """Currently unused"""
    CityDirection: None
    """Currently unused"""
    FlagStopNo: None
    """Currently unused"""


class Stop2(TypedDict):
    """Represents a tram stop."""

    StopID: None
    """Currently unused"""
    Description: None
    """Currently unused"""
    StopName: str
    """Name of this stop"""
    StopNo: Literal[0]
    """Currently unused"""
    DistanceToLocation: float
    """Currently unused"""
    Destination: None
    """Currently unused"""
    Suburb: None
    """Currently unused"""
    Latitude: float
    """Currently unused; will always return ``0.0``"""
    Longitude: float
    """Currently unused; will always return ``0.0``"""
    RouteNo: Literal[0]
    """Currently unused"""
    CityDirection: str
    """Descriptor of the direction of travel for this stop (e.g. towards or away from city); ``None`` if not provided"""
    FlagStopNo: str
    """Stop number of this stop as printed on the signage"""


class StopResponse(TypedDict):
    """Raw response type of ``/GetStopInformation.ashx``"""

    ResponseObject: Stop2
    """The response data"""
    ResponseString: str | None
    """Error message, if any"""
    HasError: bool
    """Whether the server reported an error"""


class StopsResponse(TypedDict):
    """Raw response type of ``/GetStopsByRouteAndDirection.ashx``"""

    ResponseObject: list[Stop1]
    """The response data"""
    ResponseString: str | None
    """Error message, if any"""
    HasError: bool
    """Whether the server reported an error"""


class RoutesResponse(TypedDict):
    """Raw response type of ``/GetPassingRoutes.ashx``"""

    ResponseObject: list[dict[Literal["RouteNo"], str]]
    """The response data"""
    ResponseString: str | None
    """Error message, if any"""
    HasError: bool
    """Whether the server reported an error"""


class DisruptionMessage(TypedDict):
    """Disruption messages for the attached departure"""

    DisplayType: Literal["Text"]
    """Purpose unclear"""
    MessageCount: int
    """Number of disruption messages"""
    Messages: list[str]
    """Descriptions of the disruptions affecting this service"""


class Departure(TypedDict):
    """Represents a tram departure from a particular stop."""

    TripID: Literal[0]
    """Trip identifier; currently unused"""
    InternalRouteNo: int
    """Route identifier for this departure"""
    RouteNo: str
    """Route number of the main route that this departure belongs to"""
    HeadBoardRouteNo: str
    """Public-facing route number for this departure"""
    VehicleNo: int
    """Identifier of the tram operating this service, as printed on and inside the vehicle; ``0`` if information is not currently available"""
    Destination: str
    """Destination of this service"""
    HasDisruption: bool
    """Whether a disruption is affecting this service"""
    IsTTAvailable: bool
    """Whether real time data is available for this departure"""
    IsLowFloorTram: bool
    """Whether this tram is a low-floor tram"""
    AirConditioned: bool
    """Whether this tram has air conditioning"""
    DisplayAC: bool
    """Whether the air conditioning icon is displayed on passenger information displays for this service"""
    HasSpecialEvent: bool
    """Whether a special event is affecting or will affect this route"""
    SpecialEventMessage: str
    """Description of the special event; empty string if none"""
    PredictedArrivalDateTime: str
    """Estimated real-time departure time of this service from this stop"""
    DisruptionMessage: DisruptionMessage
    """Descriptions of the disruptions affecting this service"""
    HasPlannedOccupation: bool
    """Whether planned service changes are affecting/will affect this route"""
    PlannedOccupationMessage: str
    """Description of the planned service changes; empty string if none"""
    TramClass: Literal["W", "Z3", "A1", "A2", "B2", "C1", "C2", "D1", "D2", "E", "G", ""]
    """Class/model of the tram operating this service; empty string if information is not currently available"""
    Latitude: float
    """Latitude coordinate of the tram's current location; ``0.0`` if information is not currently available"""
    Longitude: float
    """Longitude coordinate of the tram's current location; ``0.0`` if information is not currently available"""
    OccupancyLevel: Literal["NO_DATA_AVAILABLE", "EMPTY", "MANY_SEATS_AVAILABLE", "FEW_SEATS_AVAILABLE", "STANDING_ROOM_ONLY", "FULL"]
    """Current occupancy level of the tram"""
    AVMTimestamp: str
    """Timestamp of the tram vehicle driver's systems at which the tram's data in this dataset was sent"""


class DeparturesResponse(TypedDict):
    """Raw response type of ``/GetNextPredictionsForStop.ashx``"""

    responseObject: list[Departure]
    """The response data"""
    hasError: bool
    """Whether the server reported an error"""
    hasResponse: bool
    """Whether the server responded to the request successfully"""
    errorMessage: str | None
    """Error message, if any"""
    webMethodCalled: Literal["GetNextPredictedRoutesCollection"]
    """Name of the request type"""
    timeRequested: str
    """Unix timestamp of the time of the request"""
    timeResponded: str
    """Unix timestamp of the time of the response"""
    validateInputs: bool
    """Purpose unclear"""


class Colour(TypedDict):
    """Represents the display or text colour of a route"""

    RouteNo: str
    """Tram route number"""
    Colour: str
    """6-digit RGB hexadecimal code of the colour"""


class ColourResponse(TypedDict):
    """Raw response type of ``/GetRouteColour.ashx`` and ``/GetRouteTextColour.ashx``"""

    responseObject: Colour
    """The response data"""
    hasError: bool
    """Whether the server reported an error"""
    hasResponse: bool
    """Whether the server responded to the request successfully"""
    errorMessage: str | None
    """Error message, if any"""
    webMethodCalled: Literal["GetRoutePIDColour", "GetRouteTextColour"]
    """Name of the request type"""
    timeRequested: str
    """Unix timestamp of the time of the request"""
    timeResponded: str
    """Unix timestamp of the time of the response"""
    validateInputs: bool
    """Purpose unclear"""
