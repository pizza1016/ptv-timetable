``ptv_timetable.types`` — Common constants and data types used by ``ptv_timetable`` and ``ptv_timetable.asyncapi``
==================================================================================================================


.. versionadded:: 0.4.0
    Moved common constants and types from :mod:`ptv_timetable` here so that they can be shared with :mod:`ptv_timetable.asyncapi`.

.. versionchanged:: 0.3.0
    Added :class:`_NotProvidedType` as a possible type for certain attributes; some previously returned :const:`None`, which was ambiguous.

.. py:currentmodule:: ptv_timetable.types

Summary
-------

.. autosummary::

    BUS
    COACH
    EXPAND_ALL
    EXPAND_DIRECTION
    EXPAND_DISRUPTION
    EXPAND_NONE
    EXPAND_ROUTE
    EXPAND_RUN
    EXPAND_STOP
    EXPAND_VEHICLE_DESCRIPTOR
    EXPAND_VEHICLE_POSITION
    METRO
    METROPOLITAN_TRAIN
    METRO_TRAIN
    MET_TRAIN
    NOT_PROVIDED
    REGIONAL_TRAIN
    REG_TRAIN
    TRAM
    TZ_MELBOURNE
    UUID_PATTERN
    VLINE
    _NotProvidedType
    Departure
    DeparturesResponse
    Direction
    Disruption
    FareEstimate
    Outlet
    PathGeometry
    Route
    Run
    RunInterchange
    SearchResult
    Stop
    StopAccessibility
    StopAmenities
    StopContact
    StopLocation
    StopStaffing
    StopTicket
    StoppingPattern
    TimetableData
    VehicleDescriptor
    VehiclePosition
    Wheelchair

.. py:module:: ptv_timetable.types
    :synopsis: Common constants and data types used by :mod:`ptv_timetable` and :mod:`ptv_timetable.asyncapi`

Constants
---------

    .. autodata:: NOT_PROVIDED
    .. autodata:: TZ_MELBOURNE
    .. autodata:: UUID_PATTERN

    .. py:data:: METROPOLITAN_TRAIN
        METRO_TRAIN
        MET_TRAIN
        METRO
        :type: ~typing.Literal[0]
        :value: 0

        Metropolitan trains. For use in ``route_type`` parameters

    .. autodata:: TRAM
    .. autodata:: BUS

    .. py:data:: REGIONAL_TRAIN
        REG_TRAIN
        COACH
        VLINE
        :type: ~typing.Literal[3]
        :value: 3

        Regional trains & coaches. For use in ``route_type`` parameters

    .. autodata:: EXPAND_ALL
    .. autodata:: EXPAND_STOP
    .. autodata:: EXPAND_ROUTE
    .. autodata:: EXPAND_RUN
    .. autodata:: EXPAND_DIRECTION
    .. autodata:: EXPAND_DISRUPTION
    .. autodata:: EXPAND_VEHICLE_DESCRIPTOR
    .. autodata:: EXPAND_VEHICLE_POSITION
    .. autodata:: EXPAND_NONE

Classes & methods
-----------------

    .. autoclass:: _NotProvidedType

    .. py:class:: TimetableData
        :abstract:

        Base class for API response types.

        .. automethod:: as_dict
        .. automethod:: as_tuple
        .. automethod:: load
        .. automethod:: aload

    .. autoclass:: Departure
    .. autoclass:: DeparturesResponse
    .. autoclass:: Direction
    .. autoclass:: Disruption
    .. autoclass:: FareEstimate
    .. autoclass:: Outlet
    .. autoclass:: PathGeometry
    .. autoclass:: Route
    .. autoclass:: Run
    .. autoclass:: RunInterchange
    .. autoclass:: SearchResult
    .. autoclass:: Stop
    .. autoclass:: StopAccessibility
    .. autoclass:: StopAmenities
    .. autoclass:: StopContact
    .. autoclass:: StopLocation
    .. autoclass:: StopStaffing
    .. autoclass:: StopTicket
    .. autoclass:: StoppingPattern
    .. autoclass:: VehicleDescriptor
    .. autoclass:: VehiclePosition
    .. autoclass:: Wheelchair
