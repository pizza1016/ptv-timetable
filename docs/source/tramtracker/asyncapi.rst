``tramtracker.asyncapi`` — Asynchronous I/O version of the TramTracker API wrapper
==================================================================================

.. py:currentmodule:: tramtracker.asyncapi

Summary
-------

.. autosummary::

    AsyncTramTrackerAPI
    AsyncTramTrackerAPI.create
    AsyncTramTrackerAPI.get_route_colour
    AsyncTramTrackerAPI.get_route_text_colour
    AsyncTramTrackerAPI.get_stop
    AsyncTramTrackerAPI.list_destinations
    AsyncTramTrackerAPI.list_routes_for_stop
    AsyncTramTrackerAPI.list_stops
    AsyncTramTrackerAPI.next_trams
    AsyncTramTrackerAPI.request

.. py:module:: tramtracker.asyncapi
    :synopsis: Asynchronous I/O version of the TramTracker API wrapper

    .. versionadded:: 0.4.0

Classes & methods
-----------------

    .. py:class:: AsyncTramTrackerAPI(session, *, calls=1, period=10)

        Creates a new :class:`AsyncTramTrackerAPI` instance.

        :param session:  Calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` to be used as a context manager. If you wish to let the instance handle the session, use the alternative constructor method :meth:`create` instead
        :type session:   ~aiohttp.ClientSession
        :param calls:    Maximum number of calls that can be made to the service within the specified ``period``
        :param period:   Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count

        .. versionchanged:: 0.5.0
            Increased default rate limit from 1 call per 10 seconds to 20 calls per 60 seconds.

        .. automethod:: create
        .. automethod:: request
        .. automethod:: get_route_colour(route_id, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
        .. automethod:: get_route_text_colour(route_id, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
        .. automethod:: get_stop
        .. automethod:: list_destinations
        .. automethod:: list_routes_for_stop
        .. automethod:: list_stops
        .. automethod:: next_trams(stop_id, route_id=None, low_floor_tram=False, as_of=datetime.datetime.now(tz=zoneinfo.ZoneInfo("Australia/Melbourne"))
