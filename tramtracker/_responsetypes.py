from typing import TypedDict, Literal


type TramTrackerResponse = DestinationsResponse | StopResponse | StopsResponse | RoutesResponse | DeparturesResponse | ColourResponse


class Destination(TypedDict):

    RouteNo: int
    InternalRouteNo: int
    AlphaNumericRouteNo: str | None
    Destination: str
    IsUpDestination: bool
    HasLowFloor: bool


class DestinationsResponse(TypedDict):

    ResponseObject: list[Destination]
    ResponseString: str | None
    HasError: bool


class Stop(TypedDict):

    StopID: None
    Description: str | None
    StopName: str
    StopNo: int
    DistanceToLocation: float
    Destination: str | None
    Suburb: str | None
    Latitude: float
    Longitude: float
    RouteNo: int
    CityDirection: str | None
    FlagStopNo: str | None


class StopResponse(TypedDict):

    ResponseObject: Stop
    ResponseString: str | None
    HasError: bool


class StopsResponse(TypedDict):

    ResponseObject: list[Stop]
    ResponseString: str | None
    HasError: bool


class RoutesResponse(TypedDict):

    ResponseObject: list[dict[Literal["RouteNo"], str]]
    ResponseString: str | None
    HasError: bool


class DisruptionMessage(TypedDict):

    DisplayType: Literal["Text"]
    MessageCount: int
    Messages: list[str]


class Departure(TypedDict):

    TripID: int
    InternalRouteNo: int
    RouteNo: str
    HeadBoardRouteNo: str
    VehicleNo: int
    Destination: str
    HasDisruption: bool
    IsTTAvailable: bool
    IsLowFloorTram: bool
    AirConditioned: bool
    DisplayAC: bool
    HasSpecialEvent: bool
    SpecialEventMessage: str
    PredictedArrivalDateTime: str
    DisruptionMessage: DisruptionMessage
    HasPlannedOccupation: bool
    PlannedOccupationMessage: str
    TramClass: Literal["W", "Z3", "A1", "A2", "B2", "C1", "C2", "D1", "D2", "E", "G", ""]
    Latitude: float
    Longitude: float
    OccupancyLevel: Literal["NO_DATA_AVAILABLE", "EMPTY", "MANY_SEATS_AVAILABLE", "FEW_SEATS_AVAILABLE", "STANDING_ROOM_ONLY", "FULL"]
    AVMTimestamp: str


class DeparturesResponse(TypedDict):

    responseObject: list[Departure]
    hasError: bool
    hasResponse: bool
    errorMessage: str | None
    webMethodCalled: Literal["GetNextPredictedRoutesCollection"]
    timeRequested: str
    timeResponded: str
    validateInputs: bool


class Colour(TypedDict):

    RouteNo: str
    Colour: str


class ColourResponse(TypedDict):

    responseObject: Colour
    hasError: bool
    hasResponse: bool
    errorMessage: str | None
    webMethodCalled: Literal["GetRoutePIDColour", "GetRouteTextColour"]
    timeRequested: str
    timeResponded: str
    validateInputs: bool
