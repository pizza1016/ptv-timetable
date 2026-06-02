# Changelog

## 0.5.0 (2026-06-01)
- Breaking change: Python minimum version requirement updated from 3.12 to 3.14
- Breaking change: New internal module `ptv_timetable._responsemodel` to model the structure of the raw JSON response data transmitted by the server
  - Signatures and type hints in `ptv_timetable`, `ptv_timetable.asyncapi` and `ptv_timetable.types` modules modified to use the `_responsemodel` module
  - The `ptv_timetable._PTVResponseType`, `ptv_timetable._FareEstimateResponseType`, `ptv_timetable.asyncapi._PTVResponseType` and `ptv_timetable.asyncapi._FareEstimateResponseType` `TypedDict`s have all consequently been deleted
  - Updated type hints and docstrings to reflect new metadata and observations
- New internal module `tramtracker._responsemodel` to model the structure of the raw JSON response data transmitted by the server
  - Updated return type of `tramtracker.TramTrackerAPI.request()` and `tramtracker.asyncapi.AsyncTramTrackerAPI.request()`
- Breaking changes in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - Type alias `RouteType` has been renamed to `RouteTypeType` as it is the type of route types, not the type of routes
    - It has also been moved to `ptv_timetable.types`; see below
  - `build_arg_string()` static method has been fully replaced with `generate_url_params()` with an entirely different signature
  - `call()` has been renamed to `request()`
  - `_encode_url()` has been renamed to `_sign()`
  - `fare_estimate()` has been renamed to `get_fare_estimate()`
  - Consequential edits to other methods to use the new and renamed methods, including renaming local `req` variables to `path`
  - `include_advertised_interchange` parameter has been removed from `list_departures()` as it is no longer supported by the API
  - Added new parameter `is_overlap_zone` to `get_fare_estimate()`, with the parameter positioned before the existing `route_types` parameter
- Breaking changes in `ptv_timetable.types`:
  - `RouteServiceStatus` is now a data class instead of a `TypedDict` (in `Route.route_service_status`)
  - In data class `PathGeometry`, fields `valid_from` and `valid_to` are now `date` objects, and the path strings in `paths` have been parsed into lists of coordinate pairs
  - In data class `StopLocation`, fields `second_stop_name` and `road_type_second` were renamed to `secondary_stop_name` and `road_type_secondary`, respectively
  - Type of `StopAmenities.car_parking` reverted to `str` (source data type) as the value may contain symbols (e.g. "+")
- Breaking changes in `tramtracker.TramTrackerAPI` and `tramtracker.asyncapi.AsyncTramTrackerAPI`:
  - `call()` has been renamed to `request()`
  - `request()` now returns the full server response (previously it didn't return the wrapping object that contained the metadata); to access the actual data, access the value at the `ResponseObject` or `responseObject` keys (whichever exists)
- Breaking changes in `tramtracker.types`:
  - In `TramStop`, the field `stop_name_and_number` has been deleted; use fields `stop_name` and `stop_number` instead
  - The following fields have been updated to return the response from the server as-is without converting zero or empty values to `None` so that consistency with the `ptv_timetable` modules is maintained: `TramDeparture.vehicle_id`, `TramDeparture.vehicle_class`, `TramDeparture.special_event_message`, `TramDeparture.planned_occupation_message`, `TramStop.location`, `TramStop.route_id` and `TramStop.distance_to_location`
- Breaking change in `vline`:
  - `next_services()` has been replaced with `next_services_factory()`, which produces a `next_services()` function but allows rate-limiting to be customised
- Other changes in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - Type aliases `RouteTypeType` (as renamed above) and `ExpandType` have been moved to `ptv_timetable.types` as part of the introduction of type annotations (but remain accessible from the base modules)
  - Added new parameter `include_advertised_interchange` to `list_stops()`
  - Added new parameter `is_overlap_zone` to `get_fare_estimate()`
  - Added overloads to `get_route()` to indicate that `geopath_date` should only be provided if `include_geopath` is `True`
  - Changed `list_disruptions()` and `list_outlets()` overload signatures to permit intermediate positional `None` arguments instead of requiring keyword arguments
  - Simplified `search()` overload signatures
  - Updated method signatures to use new annotated types in `ptv_timetable.types`; `ExpandType` and `RouteTypeType` type aliases also moved to that module
- Other changes in `ptv_timetable.types`:
  - Added annotated types in compatibility with the [annotated-types](https://github.com/annotated-types/annotated-types) package
  - Added `ParseError` and `@_error_wrapper`, and decorated the `.load()` and `.aload()` methods to allow the raw response data causing an exception in the parsing stage to be identified
  - Added `Run.external_service` (recently added by server, but purpose is unclear)
  - Abstract method `TimetableData.load()` now raises `NotImplementedError`
  - Notes about possible deprecation removed and type hints updated for some fields as usages, albeit rare, have been found
  - `VehiclePosition.direction` can be `None`
  - Added new possible value for `Disruption.disruption_type`
- Other change in `tramtracker.TramTrackerAPI` and `tramtracker.asyncapi.AsyncTramTrackerAPI`:
  - Switched TramTracker API access from HTTP to HTTPS
- Other change in `tramtracker.types`:
  - In `TramDeparture`, added new API data fields: `location`, `occupancy_level` and `AVM_timestamp`
- Increased API rate limits of `ptv_timetable` and `tramtracker` to 20 calls per 60 seconds
- Fixed bugs (general):
  - The first parameter (`cls`) of class methods is now of type `type[Self]` instead of the erroneous `Self`
  - The `vline` module wasn't actually included in the published package
- Fixed bugs in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - `geopath_date` value in `get_route()` was not converted to string before being sent to the API
  - A `None` argument check for the `date` parameter was missing in `get_run()`
  - Some URL parameter names in `get_fare_estimate()` were incorrect
  - `get_fare_estimate()` can return `None`
  - Corrected overload signatures in `search()`
- Fixed bug in `tramtracker.TramTrackerAPI` and `tramtracker.asyncapi.AsyncTramTrackerAPI`:
  - The data source of the `up_direction` field in the return value of `list_destinations()` has a new name
- Fixed bugs in `ptv_timetable.types`:
  - `RunInterchange` was absent from `__all__`
  - `Run.interchange` `dict` values weren't converted to `RunInterchage` instances
- Added some unit tests
- Updated documentation

## 0.4.1 (2025-03-17)
- Created full API reference
  - Consequential edits to docstrings
  - Type hinting fixes

## 0.4.0 (2025-02-28)
- New modules `ptv_timetable.asyncapi` and `tramtracker.asyncapi` to allow for asynchronous operations using the built-in `asyncio` library
  - Consequential modifications to dataclasses in `ptv_timetable.types`
- Moved constants and types in `ptv_timetable` and `tramtracker` to `ptv_timetable.types` and `tramtracker.types`, respectively (they are still accessible from `ptv_timetable` and `tramtracker`)
- Breaking change: `tramtracker.TramTrackerService` has been renamed to `tramtracker.TramTrackerAPI`
- An instance of `ptv_timetable.TimetableAPI` and `tramtracker.TramTrackerAPI` now uses a single `requests.sessions.Session` instance for all calls made through it (instead of using `requests.get()` which creates a new session on each call)
  - Added the `session` parameter to the constructors of `ptv_timetable.TimetableAPI` and `tramtracker.TramTrackerAPI`
- Type hinting adjustments
  - Added `ptv_timetable._PTVResponseType`, `ptv_timetable._FareEstimateResponseType`, `ptv_timetable.asyncapi._PTVResponseType` and `ptv_timetable.asyncapi._FareEstimateResponseType`, which are all `TypedDict` subclasses, and made consequential type hint changes
  - Replaced `dict` hint with `typing.TypedDict` in return type of `ptv_timetable.list_disruption_modes()`
  - Added missing return types in overloaded signatures of `ptv_timetable.search()`
- Fixed bugs:
  - Stray `PathGeometry()` in `ptv_timetable.types.Route.load()` from earlier version (now `PathGeometry.load()`)
  - Removed old `kwargs.pop("direction")` line in `ptv_timetable.types.Route.load()` that has since been replaced
- Updated documentation and metadata

## 0.3.1 (2025-01-14)
- Added dataclass `ptv_timetable.types.RunInterchange`
- Added property `ptv_timetable.types.Departure.departure_time`
- Error logging in `vline` module
- Type hinting adjustments
  - Replaced `dict` hint with `typing.TypedDict` in `ptv_timetable.types.Stop.interchange`
  - `ptv_timetable.types.StopAccessibility.platform_number` is a `str`, not `int`
- Fixed bugs:
  - Incomplete type hint in `ptv_timetable.TimetableAPI.call()`
- Update data licensing information
  - Yarra Trams is now operated by Yarra Journey Makers Pty Ltd

## 0.3.0 (2024-12-12)
- Added new `vline` module to retrieve real-time platform information and estimated V/Line train departure/arrival at Southern Cross station
  - Added V/Line copyright information to `LICENCE.md`
- Added a new sentinel value `NOT_PROVIDED` to `ptv_timetable.types` to be used when an API operation doesn't contain a particular field
- Clarified some code in `ptv_timetable.types`
- Type hinting adjustments
  - Replaced some `dict` hints with `typing.TypedDict`
- Updated documentation and metadata

## 0.2.1 (2024-10-14)
- Allow customisation of rate-limiting on instantiation of `tramtracker.TramTrackerService` via the `calls` and `period` parameters
  - Breaking change: `TramTrackerService` must now be instantiated; methods are no longer class methods 
- Allow customisation of rate limit handlers on instantiation of `ptv_timetable.TimetableAPI` and `tramtracker.TramTrackerService`
- Added `.as_dict()` and `.as_tuple()` to dataclasses in `tramtracker` module
- Type hinting adjustments
  - Missed a few `typing.Final`s
  - Explicit subclassing from `object`
- Clarifications in docstrings
- Minor editorial change in `CHANGELOG.md`
- Updated documentation and metadata

## 0.2.0 (2024-09-01)
- Dataclasses in `ptv_timetable` moved to `ptv_timetable.types`
- Added `ptv_timetable.types.StoppingPattern.simple()`
- Allow customisation of rate-limiting on instantiation of `ptv_timetable.TimetableAPI` by adding the `calls` and `period` parameters
- Renamed `ptv_timetable.TimetableAPI.list_directions()` to `.get_direction()`
- Added `.as_dict()` and `.as_tuple()` to `ptv_timetable.types.TimetableData` abstract class
- Type hinting adjustments
  - Non-`typing.Literal` constants are now `typing.Final`
  - `run_ref` parameters in `ptv_timetable.TimetableAPI.get_pattern()` and `.get_run()` now also accept `int`s
- Fixed bugs:
  - Missed `f` f-string prefix in `ptv_timetable.TimetableAPI.get_direction()`
  - Stray `Stop()` in `ptv_timetable.types.StoppingPattern.load()` from earlier version (now `Stop.load()`)
  - Missed `slots=True` parameter in `@dataclasses.dataclass` decorator for `ptv_timetable.types.TimetableData`
- Updated documentation and metadata

## 0.1.2 (2024-08-12)
- Added `interchange` attribute to `ptv_timetable.Stop`
- Added `CHANGELOG.md`
- Updated `README.md` to add usage notes

## 0.1.1 (2024-07-29)
- Made logger variables private; devs should call `logging.getLogger()` to get the module loggers

## 0.1.0 (2024-07-28)
- First (pre)release!
