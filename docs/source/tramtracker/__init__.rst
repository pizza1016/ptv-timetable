``tramtracker`` — API wrapper for TramTracker
=============================================

.. py:currentmodule:: tramtracker

Summary
-------

.. autosummary::

    TramTrackerAPI
    TramTrackerAPI.get_route_colour
    TramTrackerAPI.get_route_text_colour
    TramTrackerAPI.get_stop
    TramTrackerAPI.list_destinations
    TramTrackerAPI.list_routes_for_stop
    TramTrackerAPI.list_stops
    TramTrackerAPI.next_trams
    TramTrackerAPI.request

.. py:module:: tramtracker
    :synopsis: API wrapper for TramTracker

Classes & methods
-----------------

    .. py:class:: TramTrackerAPI[**_P, _R](*, calls=1, period=10, ratelimit_handler=ratelimit.decorators.sleep_and_retry, session=None)

        Initialises a new :class:`TramTrackerAPI` instance.

        :param calls:             Maximum number of calls that can be made to the service within the specified ``period``
        :param period:            Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :param ratelimit_handler: Function decorator that handles `ratelimit.exception.RateLimitException <https://github.com/tomasbasham/ratelimit>`_ without re-raising it; defaults to `ratelimit.decorators.sleep_and_retry <https://github.com/tomasbasham/ratelimit>`_. A custom handler should match the specified signature, otherwise the program's behaviour is undefined (there is no runtime checking of the suitability of the handler)
        :param session:           If specified, calls will be made using this HTTP session; this allows a :class:`~requests.sessions.Session` to be used as a context manager (default is to create a new :class:`~requests.sessions.Session` instance to be used internally)

        .. versionchanged:: 0.2.1
            Added the ``calls``, ``period`` and ``ratelimit_handler`` parameters.

        .. versionchanged:: 0.4.0
            Renamed from ``TramTrackerService`` to ``TramTrackerAPI``. Added the ``session`` parameter.

        .. versionchanged:: 0.5.0
            Increased default rate limit from 1 call per 10 seconds to 20 calls per 60 seconds.

        .. automethod:: request
        .. automethod:: get_route_colour(route_id, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
        .. automethod:: get_route_text_colour(route_id, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
        .. automethod:: get_stop
        .. automethod:: list_destinations
        .. automethod:: list_routes_for_stop
        .. automethod:: list_stops
        .. automethod:: next_trams(stop_id, route_id=None, low_floor_tram=False, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
