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

    .. py:exception:: TramTrackerError

        Constructs a new exception instance with the specified error message. This is used to raise an exception when the TramTracker data service responds with an error.

        :param message: Error message to display
        :param args:    Any other positional-only arguments to pass to the constructor of the parent class
