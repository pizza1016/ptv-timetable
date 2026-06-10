# Victorian public transport information API wrappers for Python (pre-release)

Python utilities for interacting with real-time information for public transport in Victoria, Australia, via the [Public Transport Victoria](https://ptv.vic.gov.au) (PTV) [Timetable API](https://timetableapi.ptv.vic.gov.au/swagger/ui/index), [Yarra Trams](https://yarratrams.com.au/)' [TramTracker data service](https://tramtracker.com.au/pid.html) and the [V/Line website](https://www.vline.com.au).

Package version: 0.5.1<br />
Last updated: 10 June 2026<br />
Tested on Python version: 3.14.5

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
| [aiohttp](https://pypi.org/project/aiohttp)       | ≥ 3.13.5          |
| [aiolimiter](https://pypi.org/project/aiolimiter) | ≥ 1.2.1           |
| [ratelimit](https://pypi.org/project/ratelimit/)  | ≥ 2.2.1           |                                                                                                                     |
| [requests](https://pypi.org/project/requests/)    | ≥ 2.34.2          |                                                                                                                     |
| [tzdata](https://pypi.org/project/tzdata/)        | ≥ 2026.2          | Only required on OSes without a native [tz database](https://en.wikipedia.org/wiki/tz_database), including Windows. |

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
  - `ptv_timetable.asyncapi` is the asynchronous I/O version
  - `ptv_timetable.types` defines dataclasses used to represent returned API objects;
- `tramtracker` for interacting with the TramTracker data service;
  - `tramtracker.asyncapi` is the asynchronous I/O version
  - `tramtracker.types` defines dataclasses used to represent returned API objects; and
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

Some actions are logged under the logger names corresponding to their module names prefixed by "ptv-timetable." (e.g. `ptv-timetable.ptv_timetable`, `ptv-timetable.ptv_timetable.types`, `ptv-timetable.tramtracker.asyncapi`). Use `logging.getLogger()` to obtain the loggers and you can register your own handlers to retrieve their contents.

## Issues and error reporting

To report problems with the package or otherwise give feedback, [go to the Issues tab of the repository](https://gitlab.com/pizza1016/ptv-timetable/-/issues).

[//]: # ()
[//]: # (## Contributing)

[//]: # ()
[//]: # (All constructive contributions are welcome! By contributing, you agree to license your contributions under the Apache Licence 2.0.)

## Copyright and licensing

This project's source code is licensed under the Apache Licence 2.0; however, data obtained from the APIs themselves via these modules are licensed separately: PTV Timetable API data are under a Creative Commons Attribution 4.0 International licence, and TramTracker and V/Line data is proprietary. See [LICENCE.md](https://gitlab.com/pizza1016/ptv-timetable/-/blob/trunk/LICENCE.md) for further information.
