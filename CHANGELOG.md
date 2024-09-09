# Changelog

## 0.2.1 (pending)
- Allow customisation of rate-limiting on `tramtracker.TramTrackerClient` by adding the `calls` and `period` class properties
- Added `.as_dict()` and `.as_tuple()` to dataclasses in `tramtracker` module
- Type hinting adjustments
  - Missed a few `typing.Final`s
  - Explicit subclassing from `object`
- Clarifications in docstrings

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
