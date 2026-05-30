``ptv_timetable.asyncapi`` — Asynchronous I/O version of the PTV Timetable API wrapper
======================================================================================

.. py:currentmodule:: ptv_timetable.asyncapi

Summary
-------

.. autosummary::

    AsyncTimetableAPI
    AsyncTimetableAPI.create
    AsyncTimetableAPI.generate_url_params
    AsyncTimetableAPI.get_direction
    AsyncTimetableAPI.get_disruption
    AsyncTimetableAPI.get_fare_estimate
    AsyncTimetableAPI.get_pattern
    AsyncTimetableAPI.get_route
    AsyncTimetableAPI.get_run
    AsyncTimetableAPI.get_stop
    AsyncTimetableAPI.list_departures
    AsyncTimetableAPI.list_disruption_modes
    AsyncTimetableAPI.list_disruptions
    AsyncTimetableAPI.list_outlets
    AsyncTimetableAPI.list_route_directions
    AsyncTimetableAPI.list_route_types
    AsyncTimetableAPI.list_routes
    AsyncTimetableAPI.list_runs
    AsyncTimetableAPI.list_stops
    AsyncTimetableAPI.list_stops_near_location
    AsyncTimetableAPI.request
    AsyncTimetableAPI.search

.. py:module:: ptv_timetable.asyncapi
    :synopsis: Wrapper for the PTV Timetable API

Constants
---------

    .. py:data:: METROPOLITAN_TRAIN
        METRO_TRAIN
        MET_TRAIN
        METRO
        :type: ~typing.Literal[0]
        :value: 0
        :canonical: ptv_timetable.types.METROPOLITAN_TRAIN
        :no-index:

        Metropolitan trains. For use in ``route_type`` parameters

    .. py:data:: TRAM
        :type: ~typing.Literal[1]
        :value: 1
        :canonical: ptv_timetable.types.TRAM
        :no-index:

        Metropolitan trams. For use in ``route_type`` parameters

    .. py:data:: BUS
        :type: ~typing.Literal[2]
        :value: 2
        :canonical: ptv_timetable.types.BUS
        :no-index:

        Metropolitan & regional buses. For use in ``route_type`` parameters

    .. py:data:: REGIONAL_TRAIN
        REG_TRAIN
        COACH
        VLINE
        :type: ~typing.Literal[3]
        :value: 3
        :canonical: ptv_timetable.types.REGIONAL_TRAIN
        :no-index:

        Regional trains & coaches. For use in ``route_type`` parameters

    .. py:data:: EXPAND_ALL
        :type: ~typing.Literal["All"]
        :value: "All"
        :canonical: ptv_timetable.types.EXPAND_ALL
        :no-index:

        Return all object properties in full. For use in ``expand`` parameters

    .. py:data:: EXPAND_STOP
        :type: ~typing.Literal["Stop"]
        :value: "Stop"
        :canonical: ptv_timetable.types.EXPAND_STOP
        :no-index:

        Return stop properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_ROUTE
        :type: ~typing.Literal["Route"]
        :value: "Route"
        :canonical: ptv_timetable.types.EXPAND_ROUTE
        :no-index:

        Return route properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_RUN
        :type: ~typing.Literal["Run"]
        :value: "Run"
        :canonical: ptv_timetable.types.EXPAND_RUN
        :no-index:

        Return run properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_DIRECTION
        :type: ~typing.Literal["Direction"]
        :value: "Direction"
        :canonical: ptv_timetable.types.EXPAND_DIRECTION
        :no-index:

        Return direction properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_DISRUPTION
        :type: ~typing.Literal["Disruption"]
        :value: "Disruption"
        :canonical: ptv_timetable.types.EXPAND_DISRUPTION
        :no-index:

        Return disruption properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_VEHICLE_DESCRIPTOR
        :type: ~typing.Literal["VehicleDescriptor"]
        :value: "VehicleDescriptor"
        :canonical: ptv_timetable.types.EXPAND_VEHICLE_DESCRIPTOR
        :no-index:

        Return vehicle descriptor properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_VEHICLE_POSITION
        :type: ~typing.Literal["VehiclePosition"]
        :value: "VehiclePosition"
        :canonical: ptv_timetable.types.EXPAND_VEHICLE_POSITION
        :no-index:

        Return vehicle position properties. For use in ``expand`` parameters

    .. py:data:: EXPAND_NONE
        :type: ~typing.Literal["None"]
        :value: "None"
        :canonical: ptv_timetable.types.EXPAND_NONE
        :no-index:

        Don't return any object properties. For use in ``expand`` parameters

Classes & methods
-----------------

    .. py:class:: AsyncTimetableAPI(dev_id, key, session, *, calls=1, period=10)

        Creates a new :class:`AsyncTimetableAPI` instance with the supplied credentials.

        :param dev_id:  User ID
        :param key:     API request signing key (a UUID)
        :param session: Calls will be made using this HTTP session; this allows a :class:`~aiohttp.ClientSession` instance to be used as a context manager. If you wish to let the instance handle the session, use the alternative constructor method :meth:`create` instead
        :type session:  ~aiohttp.ClientSession
        :param calls:   Maximum number of calls that can be made to the API within the specified ``period``
        :param period:  Number of seconds since the last reset (or initialisation) at which the rate limiter will reset its call count
        :return:        The new instance

        .. automethod:: create
        .. automethod:: generate_url_params
        .. automethod:: request
        .. automethod:: get_direction
        .. automethod:: get_disruption
        .. automethod:: get_fare_estimate
        .. automethod:: get_pattern
        .. automethod:: get_route
        .. automethod:: get_run

        .. py:method:: get_stop(stop_id, route_type, stop_location=None, stop_amenities=None, stop_accessibility=None, stop_contact=None, stop_ticket=None, gtfs=None, stop_staffing=None, stop_disruptions=None)
            :async:

            Returns the stop with the specified stop identifier and route type.

            :param stop_id:            The stop identifier; must be :class:`str` if ``gtfs`` is set to ``True``; otherwise, must be :class:`int`
            :type stop_id:             int | str
            :param route_type:         The transport type of the specified stop
            :type route_type:          ~typing.Literal[0, 1, 2, 3]
            :param stop_location:      Whether to include stop location information in the result (server default is ``False``)
            :type stop_location:       bool | None
            :param stop_amenities:     Whether to include stop amenities information in the result (server default is ``False``)
            :type stop_amenities:      bool | None
            :param stop_accessibility: Whether to include stop accessibility information in the result (server default is ``False``)
            :type stop_accessibility:  bool | None
            :param stop_contact:       Whether to include operator contact details in the result (server default is ``False``)
            :type stop_contact:        bool | None
            :param stop_ticket:        Whether to include ticketing information in the result (server default is ``False``)
            :type stop_ticket:         bool | None
            :param gtfs:               Whether the value specified in ``stop_id`` is a General Transit Feed Specification identifier (server default is ``False``)
            :type gtfs:                bool | None
            :param stop_staffing:      Whether to include stop staffing information in the result (server default is ``False``)
            :type stop_staffing:       bool | None
            :param stop_disruptions:   Whether to include information about disruptions affecting the stop in the result (server default is ``False``)
            :type stop_disruptions:    bool | None
            :param typing.Self self:
            :return:                   Details of the specified stop
            :rtype:                    Stop

        .. py:method:: list_departures(route_type, stop_id, route_id=None, platform_numbers=None, direction_id=None, gtfs=None, include_advertised_interchange=None, date=None, max_results=None, include_cancelled=None, look_backwards=None, expand=None, include_geopath=None)
            :async:

            Returns a list of departures from the specified stop.

            :param route_type:                     Transport mode identifier
            :type route_type:                      ~typing.Literal[0, 1, 2, 3]
            :param stop_id:                        Stop identifier; must be :class:`str` if ``gtfs`` is set to ``True``; otherwise, must be :class:`int`
            :type stop_id:                         int | str
            :param route_id:                       If specified, show only departures for the specified route. Only one of ``route_id`` and ``platform_numbers`` should be specified.
            :type route_id:                        int | None
            :param platform_numbers:               If specified, show only departures from the specified platform numbers. Only one of ``route_id`` and ``platform_numbers`` should be specified.
            :type platform_numbers:                ~collections.abc.Iterable[str | int] | None
            :param direction_id:                   If specified, show only departures travelling towards the specified direction
            :type direction_id:                    int | None
            :param gtfs:                           Whether the value specified in stop_id is a General Transit Feed Specification identifier (server default is ``False``)
            :type gtfs:                            bool | None
            :param include_advertised_interchange: Whether to include stop interchange information in result (server default is ``False``)
            :type include_advertised_interchange:  bool | None
            :param date:                           If specified, show departures from the specified date (server default is current date). Appears to ignore the time fields. If ``look_backwards`` is ``True``, show departures that arrive at their terminating destinations prior to the specified date instead. Defaults to :class:`ZoneInfo("Australia/Melbourne") <zoneinfo.ZoneInfo>` if time zone not specified
            :type date:                            ~datetime.datetime | str | None
            :param max_results:                    If specified, limits the number of departures returned to this value
            :type max_results:                     int | None
            :param include_cancelled:              Whether to include departures that are cancelled (server default is ``False``)
            :type include_cancelled:               bool | None
            :param look_backwards:                 If set to ``True``, departures that arrive at their terminating destinations prior to the date specified in 'date' are returned instead (server default is ``False``)
            :type look_backwards:                  bool | None
            :param expand:                         Optional data to include in the response (server default is :const:`~ptv_timetable.types.EXPAND_NONE`)
            :type expand:                          ~collections.abc.Iterable[~typing.Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"]] | ~typing.Literal["All", "Stop", "Route", "Run", "Direction", "Disruption", "VehicleDescriptor", "VehiclePosition", "None"] | None
            :param include_geopath:                Include the run's path geometry (server default is ``False``)
            :type include_geopath:                 bool | None
            :param typing.Self self:
            :return:                               The requested departure information and any associated stop, route, run, direction and disruption data
            :rtype:                                ~ptv_timetable.types.DeparturesResponse

        .. automethod:: list_disruption_modes

        .. py:method:: list_disruptions(route_id=None, stop_id=None, route_types=None, disruption_modes=None, disruption_status=None)
            :async:

            Returns a list of all disruptions or, if specified, the disruptions for the specified route and/or stop.

            :param route_id:          If route identifier is specified, list only disruptions for the specified route. If both ``route_id`` and ``stop_id`` are specified, list only disruptions for the specified route and stop
            :type route_id:           int | None
            :param stop_id:           If stop identifier is specified, list only disruptions for the specified stop. If both ``route_id`` and ``stop_id`` are specified, list only disruptions for the specified route and stop
            :type stop_id:            int | None
            :param route_types:       If specified, list only disruptions for the specified travel modes. Does not work with ``route_id`` or ``stop_id``
            :type route_types:        ~collections.abc.Iterable[~typing.Literal[0, 1, 2, 3]] | ~typing.Literal[0, 1, 2, 3] | None
            :param disruption_modes:  If specified, list only disruptions for the specified disruption modes. Does not work with ``route_id`` or ``stop_id``
            :type disruption_modes:   ~collections.abc.Iterable[~typing.Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100]] | ~typing.Literal[1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 100] | None
            :param disruption_status: If specified, list only disruptions with the specified status
            :type disruption_status:  ~typing.Literal["Current", "Planned"] | None
            :param typing.Self self:
            :return:                  A list of disruptions
            :rtype:                   list[~ptv_timetable.types.Disruption]

        .. py:method:: list_outlets(latitude=None, longitude=None, max_distance=None, max_results=None)
            :async:

            Returns a list of all myki ticket outlets or, if specified, near the specified location.

            :param latitude:         If specified together with ``longitude``, return ticket outlets near the specified location only
            :type latitude:          float | None
            :param longitude:        If specified together with ``latitude``, return ticket outlets near the specified location only
            :type longitude:         float | None
            :param max_distance:     Maximum radius from the specified location to search, in metres (server default is 300 metres). Can only be used if ``latitude`` and ``longitude`` are specified
            :type max_distance:      float | None
            :param max_results:      Maximum number of outlets to be returned (server default is 30)
            :type max_results:       int | None
            :param typing.Self self:
            :return:                 A list of ticket outlets
            :rtype:                  list[~ptv_timetable.types.Outlet]

        .. automethod:: list_route_directions
        .. automethod:: list_route_types
        .. automethod:: list_routes
        .. automethod:: list_runs
        .. automethod:: list_stops
        .. automethod:: list_stops_near_location

        .. py:method:: search(search_term, route_types=None, latitude=None, longitude=None, max_distance=None, include_outlets=None, match_stop_by_locality=None, match_route_by_locality=None, match_stop_by_gtfs_stop_id=None)
            :async:

            Searches the PTV database for the specified search term and returns the matching stops, routes and ticket outlets.

            If the search term is numeric or has fewer than 3 characters, the API will only return routes.

            :param str search_term:            Term to search
            :param route_types:                Return stops and routes with the specified travel mode type(s) only
            :type route_types:                 ~collections.abc.Iterable[~typing.Literal[0, 1, 2, 3]] | ~typing.Literal[0, 1, 2, 3] | None
            :param latitude:                   Latitude coordinate of the location to search
            :type latitude:                    float | None
            :param longitude:                  Longitude coordinate of the location to search
            :type longitude:                   float | None
            :param max_distance:               Radius, from centre location (specified in latitude and longitude parameters), of area to search in, in metres (server default is 300 metres). Can only be used if ``latitude`` and ``longitude`` are specified
            :type max_distance:                float | None
            :param include_outlets:            Whether to include ticket outlets in search result (server default is ``True``)
            :type include_outlets:             bool | None
            :param match_stop_by_locality:     Whether to include stops in the search result where their localities match the search term (server default is ``True``)
            :type match_stop_by_locality:      bool | None
            :param match_route_by_locality:    Whether to include routes in the search result where their localities match the search term (server default is ``True``)
            :type match_route_by_locality:     bool | None
            :param match_stop_by_gtfs_stop_id: Whether to include stops in the search result when the search term is treated as a General Transit Feed Specification stop identifier (server default is ``False``)
            :type match_stop_by_gtfs_stop_id:  bool | None
            :param typing.Self self:
            :return:                           All matching stops, routes and ticket outlets
            :rtype:                            ~ptv_timetable.types.SearchResult
