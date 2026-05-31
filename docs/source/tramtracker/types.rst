``tramtracker.types`` — Common constants and data types used by ``tramtracker`` and ``tramtracker.asyncapi``
============================================================================================================

.. versionadded:: 0.4.0
    Moved common constants and types from :mod:`tramtracker` here so that they can be shared with :mod:`tramtracker.asyncapi`.

.. py:currentmodule:: tramtracker.types

Summary
-------

.. autosummary::

    TramDeparture
    TramDestination
    TramStop
    TramTrackerData
    TramTrackerError

.. py:module:: tramtracker.types
    :synopsis: Common constants and data types used by :mod:`tramtracker` and :mod:`tramtracker.asyncapi`

Constants
---------

    .. autodata:: EPOCH
    .. autodata:: TIMESTAMP_PATTERN
    .. autodata:: TZ_MELBOURNE

Classes & methods
-----------------

    .. autoclass:: TramTrackerData
    .. autoclass:: TramDeparture
    .. autoclass:: TramDestination
    .. autoclass:: TramStop

    .. autoexception:: TramTrackerError
