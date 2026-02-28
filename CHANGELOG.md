# Changelog

## 0.5.0 (2026-\_\_-\_\_)
- Breaking changes in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - `build_arg_string()` static method has been fully replaced with `generate_url_params()` with an entirely different signature
  - `call()` has been renamed to `request()`
  - `_encode_url()` has been renamed to `_sign()`
  - `fare_estimate()` has been renamed to `get_fare_estimate()`
  - Consequential edits to other methods to use the new and renamed methods, including renaming local `req` variables to `path`
  - `include_advertised_interchange` parameter has been removed from `list_departures()` as it is no longer supported by the API
  - Added new parameter `is_overlap_zone` to `get_fare_estimate()`, with the parameter positioned before the existing `route_types` parameter
- Breaking change in `ptv_timetable.types`:
  - In dataclass `StopLocation`, fields `second_stop_name` and `road_type_second` were renamed to `secondary_stop_name` and `road_type_secondary`, respectively
- Other changes in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - Added new parameter `include_advertised_interchange` to `list_stops()`
  - Added new parameter `is_overlap_zone` to `get_fare_estimate()`
  - Added overloads to `get_route()` to indicate that `geopath_date` should only be provided if `include_geopath` is `True`
  - Changed `list_disruptions()` and `list_outlets()` overload signatures to permit intermediate positional `None` arguments instead of requiring keyword arguments
- Fixed bugs in `ptv_timetable.TimetableAPI` and `ptv_timetable.asyncapi.AsyncTimetableAPI`:
  - `geopath_date` value in `get_route()` was not converted to string before being sent to the API
  - Some URL parameter names in `get_fare_estimate()` were incorrect
  - `get_fare_estimate()` can return `None`
  - Corrected overload signatures in `search()`
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
