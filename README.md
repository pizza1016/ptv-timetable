# Victorian public transport information API wrappers for Python (pre-release)

Python utilities for interacting with real-time information for public transport in Victoria, Australia, via the [Public Transport Victoria](https://ptv.vic.gov.au) (PTV) [Timetable API](https://timetableapi.ptv.vic.gov.au/swagger/ui/index), [Yarra Trams](https://yarratrams.com.au/)' [TramTracker data service](https://tramtracker.com.au/pid.html) and the [V/Line website](https://www.vline.com.au).

Package version: 0.4.1<br />
Last updated: 17 March 2025<br />
Tested on Python version: ≥ 3.12

This repository is hosted on GitLab and mirrored on GitHub. **If you are viewing on GitHub, please send any issues, comments and feedback [there](https://gitlab.com/pizza1016/ptv-timetable).**

---

## Documentation

The full public API documentation can be found at: https://pizza1016.gitlab.io/ptv-timetable 

## Overview

This package of modules aims to simplify the process of retrieving and manipulating real-time data for public transport in Victoria, Australia and document each operation and response supported by the APIs.

The package implements interfaces for three data sources:
- PTV [Timetable API](https://timetableapi.ptv.vic.gov.au/swagger/ui/index) - the main service for real-time and scheduled public transport information across Victoria;
- Yarra Trams [TramTracker](https://tramtracker.com.au/pid.html) - live passenger information for the Melbourne tram network, including planned diversions which the Timetable API lacks; and
- [V/Line website](https://www.vline.com.au) - since November 2024, real-time V/Line departures and arrivals information at Southern Cross station for the next 30 minutes, including platform information and estimated time of departure/arrival.

The package minimises the use of third-party modules to improve portability, especially on systems with restrictions.

### What's different from accessing the Timetable API directly?

- **Simplifying output "types"**: instead of having a different response schema for each API operation, any object that represents the same concept are consolidated into the same response type (e.g. all responses that represent a public transport stop are instances of the same class: `Stop`, instead of the ten or so different representations in the API). Any attribute/field for which the API does not provide a response for will have a sentinel value.
- **Best-effort documentation**: all operations and fields have, as far as practicable, been documented in type hints and docstrings (although some of these are guesses).
- **Date and time representation**: date inputs and outputs are converted from and to `datetime` objects with the local time zone of Victoria, so that you do not have to deal with the different string representations of dates and speaking to the API in the UTC time zone as implemented by the Timetable API.
- **Other quality of life modifications**: such as consistent attribute names, fixing typos and removing trailing whitespaces.

## Pre-release package

This package is in pre-release. Breaking changes may be made without notice during development.

## Direct dependencies
Note that these dependencies may have their own dependencies.

| Package name                                      | Tested on version | Notes                                                                                                               |
|---------------------------------------------------|-------------------|---------------------------------------------------------------------------------------------------------------------|
| [aiohttp](https://pypi.org/project/aiohttp)       | ≥ 3.11.11         |
| [aiolimiter](https://pypi.org/project/aiolimiter) | ≥ 1.2.1           |
| [ratelimit](https://pypi.org/project/ratelimit/)  | ≥ 2.2.1           |                                                                                                                     |
| [requests](https://pypi.org/project/requests/)    | ≥ 2.32.3          |                                                                                                                     |
| [tzdata](https://pypi.org/project/tzdata/)        | ≥ 2024.1          | Only required on OSes without a native [tz database](https://en.wikipedia.org/wiki/tz_database), including Windows. |

## Installation

The recommended method to install this package is via the [Python Package Index](https://pypi.org/project/ptv-timetable/) (PyPI):
```bash
python -m pip install ptv-timetable
```
You can also install from the [GitLab Package Registry](https://gitlab.com/pizza1016/ptv-timetable/-/packages/) (authentication not required):
```bash
python -m pip install --index-url https://gitlab.com/api/v4/projects/54559866/packages/pypi/simple ptv-timetable
```
These commands will also install any required dependencies from PyPI.

## Usage

This package adds three modules into the root namespace of your interpreter (so they can be directly imported into your code with `import <module_name>`):
- `ptv_timetable` for interacting with the PTV Timetable API;
  - `ptv_timetable.types` defines dataclasses used to represent returned API objects;
- `tramtracker` for interacting with the TramTracker data service; and
- `vline` for retrieving V/Line Southern Cross departure and arrival information.

Each module defines data types that encapsulate the responses from the APIs to allow access by attribute reference (`.`) to take advantage of autocompletion systems in IDEs where available. This format also allows each field to be documented, which is not a feature that is available in the raw `dict`s returned by the APIs.

### PTV Timetable API

To use the Timetable API service, you will first need to obtain credentials from PTV:
- Send an email to [APIKeyRequest@ptv.vic.gov.au](mailto:APIKeyRequest@ptv.vic.gov.au) with the subject line `PTV Timetable API - request for key`.
- You will receive a user ID and a UUID-format signing key in response. This may take several days depending on volume of requests; you will *not* receive confirmation that your request was received, so hang tight!<br />
 (Details: http://ptv.vic.gov.au/ptv-timetable-api/)

Import the `ptv_timetable` module:
```python
from ptv_timetable import *
```

This adds the `TimetableAPI` class and a number of constants for use in method arguments.

Create a new instance of `TimetableAPI` and provide your user ID and signing key:
```python
timetable = TimetableAPI(dev_id, key)
```

You can now communicate with the API using the instance methods.

There is also an `asyncio` version, which you can set up as follows:
```python
import asyncio

from aiohttp.client import ClientSession
from ptv_timetable.asyncapi import *

async def main() -> None:
    async with ClientSession() as session:
        timetable = AsyncTimetableAPI(dev_id, key, session)
        # Your code here
        # e.g. routes = await timetable.list_routes(METROPOLITAN_TRAIN)
    return

if __name__ == "__main__":
    asyncio.run(main())
```

### TramTracker data service
Import the `tramtracker` module and instantiate `TramTrackerAPI`:
```python
from tramtracker import *

tracker = TramTrackerAPI()

# Your code here
```

Or, for asynchronous use:
```python
import asyncio

from aiohttp.client import ClientSession
from tramtracker.asyncapi import *

async def main() -> None:
    async with ClientSession() as session:
        tracker = AsyncTramTrackerAPI(session)
        # Your code here
    return

if __name__ == "__main__":
    asyncio.run(main())
```

### Southern Cross station V/Line departures and arrivals
Import the `vline` module and call `next_services()`:
```python
import vline

departures, arrivals, as_at = vline.next_services()
```

### Logging

Some actions are logged under the logger names `ptv-timetable.ptv_timetable`, `ptv-timetable.tramtracker` and `ptv-timetable.vline`. Use `logging.getLogger()` to obtain the loggers and you can register your own handlers to retrieve their contents.

## Issues and error reporting

To report problems with the package or otherwise give feedback, [go to the Issues tab of the repository](https://gitlab.com/pizza1016/ptv-timetable/-/issues).

[//]: # ()
[//]: # (## Contributing)

[//]: # ()
[//]: # (All constructive contributions are welcome! By contributing, you agree to license your contributions under the Apache Licence 2.0.)

## Copyright and licensing

This project's source code is licensed under the Apache Licence 2.0; however, data obtained from the APIs themselves via these modules are licensed separately: PTV Timetable API data are under a Creative Commons Attribution 4.0 International licence and TramTracker data is proprietary. See [LICENCE.md](https://gitlab.com/pizza1016/ptv-timetable/-/blob/trunk/LICENCE.md) for further information.

## Summary of module contents

### ptv_timetable/\_\_init__.py

| Constant/function/method                                                                                                                                                                                                                                     | Description                                                                                                                                                                                                            |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **METROPOLITAN_TRAIN<br/>METRO_TRAIN<br/>MET_TRAIN<br/>METRO**                                                                                                                                                                                               | Use in `route_type` parameters to specify the metropolitan train network.                                                                                                                                              |
| **TRAM**                                                                                                                                                                                                                                                     | Use in `route_type` parameters to specify the metropolitan tram network.                                                                                                                                               |
| **BUS**                                                                                                                                                                                                                                                      | Use in `route_type` parameters to specify the metropolitan or regional bus network.                                                                                                                                    |
| **REGIONAL_TRAIN<br/>REG_TRAIN<br/>COACH<br/>VLINE**                                                                                                                                                                                                         | Use in `route_type` parameters to specify the regional train or coach network.                                                                                                                                         |
| **EXPAND_**<_property_>                                                                                                                                                                                                                                      | Use in `expand` parameters to tell the API to return the specified properties in full.                                                                                                                                 |
| _class_ **TimetableAPI(**_dev_id, key, *, calls=1, period=10, ratelimit_handler=ratelimit.decorators.sleep_and_retry, session=None_**)**                                                                                                                     | Constructs a new instance of the `TimetableAPI` class with the supplied credentials.<br/><br/>To obtain your own set of credentials, follow the instructions on [this page](http://ptv.vic.gov.au/ptv-timetable-api/). |
| TimetableAPI.**list_route_directions(**_route_id_**)**                                                                                                                                                                                                       | List directions for a specified route.<br/><br/>API operation: `/v3/directions/route/{route_id}`                                                                                                                       |
| TimetableAPI.**get_direction(**_direction_id, route_type=None_**)**                                                                                                                                                                                          | List directions with a specified identifier.<br/><br/>API operation: `/v3/directions/{direction_id}/route_type/{route_type}`                                                                                           |
| TimetableAPI.**get_pattern(**_run_ref, route_type, stop_id=None, date=None, include_skipped_stops=None, expand=None, include_geopath=None_**)**                                                                                                              | Retrieve the stopping pattern and times of arrival at each stop for a particular run.<br/><br/>API operation: `/v3/pattern/run/{run_ref}/route_type/{route_type}`                                                      |
| TimetableAPI.**get_route(**_route_id, include_geopath=None, geopath_date=None_**)**                                                                                                                                                                          | Return the route with the specified identifier.<br/><br/>API operation: `/v3/routes/{route_id}`                                                                                                                        |
| TimetableAPI.**list_routes(**_route_types=None, route_name=None_**)**                                                                                                                                                                                        | List all routes.<br/><br/>API operation: `/v3/routes/`                                                                                                                                                                 |
| TimetableAPI.**list_route_types()**                                                                                                                                                                                                                          | List all route types (modes of travel) and their identifiers.<br/><br/>API operation: `/v3/route_types/`                                                                                                               |
| TimetableAPI.**get_run(**_run_ref, route_type=None, expand=None, date=None, include_geopath=None_**)**                                                                                                                                                       | Return the run with the specified identifier.<br/><br/>API operation: `/v3/runs/{run_ref}/route_type/{route_type}`                                                                                                     |
| TimetableAPI.**list_runs(**_route_id, route_type=None, expand=None, date=None_**)**                                                                                                                                                                          | List runs for a specified route.<br/><br/>API operation: `/v3/runs/route/{route_id}/route_type/{route_type}`                                                                                                           |
| TimetableAPI.**get_stop(**_stop_id, route_type, stop_location=None, stop_amenities=None, stop_accessibility=None, stop_contact=None, stop_ticket=None, gtfs=None, stop_staffing=None, stop_disruptions=None_**)**                                            | Return the stop with the specified identifier and route type.<br/><br/>API operation: `/v3/stops/{stop_id}/route_type/{route_type}`                                                                                    |
| TimetableAPI.**list_stops(**_route_id, route_type, direction_id=None, stop_disruptions=None_**)**                                                                                                                                                            | List all stops on a specified route.<br/><br/>API operation: `/v3/stops/route/{route_id}/route_type/{route_type}`                                                                                                      |
| TimetableAPI.**list_stops_near_location(**_latitude, longitude, route_types=None, max_results=None, max_distance=None, stop_distuptions=None_**)**                                                                                                           | List all stops near a specified location.<br/><br/>API operation: `/v3/stops/location/{latitude},{longitude}`                                                                                                          |
| TimetableAPI.**list_departures(**_route_type, stop_id, route_id=None, platform_numbers=None, direction_id=None, gtfs=None, include_advertised_interchange=None, date=None, max_results=None, include_cancelled=None, expand=None, include_geopath=None_**)** | List the departures from a specified stop.<br/><br/>API operation: `/v3/departures/route_type/{route_type}/stop/{stop_id}/route/{route_id}`                                                                            |
| TimetableAPI.**list_disruptions(**_route_id=None, stop_id=None, route_types=None, disruption_modes=None, disruption_status=None_**)**                                                                                                                        | List disruptions on the network.<br/><br/>API operation: `/v3/disruptions/route/{route_id}/stop/{stop_id}`                                                                                                             |
| TimetableAPI.**list_disruption_modes()**                                                                                                                                                                                                                     | List all disruption modes.<br/><br/>API operation: `/v3/disruptions/modes`                                                                                                                                             |
| TimetableAPI.**fare_estimate(**_zone_a, zone_b, touch_on=None, touch_off=None, is_free_fare_zone=None, route_types=None_**)**                                                                                                                                | Return the fare for a specified journey.<br/><br/>API operation: `/v3/fare_estimate/min_zone/{minZone}/max_zone/{maxZone}`                                                                                             |
| TimetableAPI.**list_outlets(**_latitude=None, longitude=None, max_distance=None, max_results=None_**)**                                                                                                                                                      | List ticket outlets near a specified location.<br/><br/>API operation: `/v3/outlets/location/{latitude},{longitude}`                                                                                                   |
| TimetableAPI.**search(**_search_term, route_types=None, latitude=None, longitude=None, max_distance=None, include_outlets=None, match_stop_by_locality=None, match_route_by_locality=None, match_stop_by_gtfs_stop_id=None_**)**                             | Search for a stop, route or ticket outlet by name.<br/><br/>API operation: `/v3/search/{search_term}`                                                                                                                  |

### ptv_timetable/asyncapi.py

| Constant/function/method                                                                           | Description                                                                                                                                                                                                                                         |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| <_constant_>                                                                                       | All constants in `ptv_timetable\__init__.py` are also available here.                                                                                                                                                                               |
| _class_ **AsyncTimetableAPI(**_dev_id, key, session, *, calls=1, period=10_**)**                   | Constructs a new instance of the `AsyncTimetableAPI` class with the supplied credentials and `aiohttp.client.ClientSession` session.                                                                                                                |
| _classmethod_ AsyncTimetableAPI.**create(**_dev_id, key, session=None, *, calls=1, period=10_**)** | Constructs a new instance of the `AsyncTimetableAPI` class with the supplied credentials. This alternative constructor does not require a `ClientSession` to be provided, with the instance itself managing the opening and closing of the session. |
| _async_ AsyncTimetableAPI.**_\<method\>_(**_\<args\>_**)**                                         | All methods described in `ptv_timetable.TimetableAPI` have the same functionality here but supports `asyncio`.                                                                                                                                      |


### tramtracker/\_\_init__.py

| Constant/function/method                                                                                                                  | Description                                                         |
|-------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| _class_ **TramTrackerAPI(**_*, calls=1, period=10, ratelimit_handler=ratelimit.decorators.sleep_and_retry, session=None_**)**             | Constructs a new instance of the `TramTrackerAPI` class.            |
| TramTrackerAPI.**list_destinations()**                                                                                                    | List all destinations on the tram network.                          |
| TramTrackerAPI.**list_stops(**_route_id, up_direction_**)**                                                                               | List stops for a specified route and direction of travel.           |
| TramTrackerAPI.**get_stop(**_stop_id_**)**                                                                                                | Return details about a specified stop.                              |
| TramTrackerAPI.**list_routes_for_stop(**_stop_id_**)**                                                                                    | List the routes serving a specified stop.                           |
| TramTrackerAPI.**next_trams(**_stop_id, route_id=None, low_floor_tram=False, as_of=datetime.now(tz=ZoneInfo("Australia/Melbourne"))_**)** | List the next tram departures from a specified stop.                |
| TramTrackerAPI.**get_route_colour(**_route_id, as_of=datetime.now(tz=ZoneInfo("Australia/Melbourne"))_**)**                               | Return the route's colour on public information paraphernalia.      |
| TramTrackerAPI.**get_route_text_colour(**_route_id, as_of=datetime.now(tz=ZoneInfo("Australia/Melbourne"))_**)**                          | Return the route's text colour on public information paraphernalia. |


### tramtracker/asyncapi.py

| Constant/function/method                                                                | Description                                                                                                                                                                                                                                                                                      |
|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _class_ **AsyncTramTrackerAPI(**_session, *, calls=1, period=10_**)**                   | Constructs a new instance of the `AsyncTramTrackerAPI` class with the supplied credentials and `aiohttp.client.ClientSession` session.                                                                                                                                                           |
| _classmethod_ AsyncTramTrackerAPI.**create(**_session=None, *, calls=1, period=10_**)** | Constructs a new instance of the `AsyncTramTrackerAPI` class with the supplied credentials and `aiohttp.client.ClientSession` session. This alternative constructor does not require a `ClientSession` to be provided, with the instance itself managing the opening and closing of the session. |
| _async_ AsyncTramTrackerAPI.**\<_method_\>(**_\<args\>_**)**                            | All methods described in `tramtracker.TramTrackerAPI` have the same functionality here but supports `asyncio`.                                                                                                                                                                                   |

### vline/\_\_init__.py

| Constant/function/method | Description                                                                                        |
|--------------------------|----------------------------------------------------------------------------------------------------|
| **next_services()**      | Gets the details of the next 30 minutes of services departing and arriving Southern Cross station. |
