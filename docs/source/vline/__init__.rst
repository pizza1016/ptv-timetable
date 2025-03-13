``vline`` — Interface for retrieving live passenger information from the V/Line website
=======================================================================================

.. py:currentmodule:: vline

Summary
-------

.. autosummary::

    Arrival
    Departure
    next_services

.. py:module:: vline
    :synopsis: Interface for retrieving live passenger information from the V/Line website

Type aliases
------------
    .. py:type:: PlatformNumber
        :canonical: ~typing.Literal["1", "2", "2A", "2B", "3", "3A", "3B", "4", "4A", "4B", "5", "5A", "5B", "6", "6A", "6B", "7", "7A", "7B", "8", "8A", "8B", "8S", "15", "15A", "15B", "16", "16A", "16B"]

Classes & methods
-----------------

    .. autoclass:: Arrival
        :exclude-members: as_dict, as_tuple

        .. py:method:: as_dict[_T](*, dict_factory=None)

            Returns this instance's fields as a :class:`dict`. The result can be customised by providing a ``dict_factory`` function.

            This is a convenient shorthand for :func:`dataclasses.asdict(self) <dataclasses.asdict>`.

            :param dict_factory: If specified, dict creation will be customised with this function
            :type dict_factory:  ~collections.abc.Callable[[list[tuple[str, str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]]], _T] | None
            :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``
            :rtype:              _T | dict[str, str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]

        .. py:method:: as_tuple[_T](*, tuple_factory=None)

            Returns this instance's fields' values as a :class:`tuple`, in order of declaration. The result can be customised by providing a ``tuple_factory`` function.

            This is a convenient shorthand for :func:`dataclasses.astuple(self) <dataclasses.astuple>`.

            :param tuple_factory: If specified, tuple creation will be customised with this function
            :type tuple_factory:  ~collections.abc.Callable[[list[str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]], _T] | None
            :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``
            :rtype:              _T | tuple[~datetime.datetime, str, PlatformNumber, ~datetime.timedelta]


    .. autoclass:: Departure
        :exclude-members: as_dict, as_tuple

        .. py:method:: as_dict[_T](*, dict_factory=None)

            Returns this instance's fields as a :class:`dict`. The result can be customised by providing a ``dict_factory`` function.

            This is a convenient shorthand for :func:`dataclasses.asdict(self) <dataclasses.asdict>`.

            :param dict_factory: If specified, dict creation will be customised with this function
            :type dict_factory:  ~collections.abc.Callable[[list[tuple[str, str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]]], _T] | None
            :return:             The result of ``dataclasses.asdict(self) if dict_factory is None else dataclasses.asdict(self, dict_factory=dict_factory)``
            :rtype:              _T | dict[str, str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]

        .. py:method:: as_tuple[_T](*, tuple_factory=None)

            Returns this instance's fields' values as a :class:`tuple`, in order of declaration. The result can be customised by providing a ``tuple_factory`` function.

            This is a convenient shorthand for :func:`dataclasses.astuple(self) <dataclasses.astuple>`.

            :param tuple_factory: If specified, tuple creation will be customised with this function
            :type tuple_factory:  ~collections.abc.Callable[[list[str | ~datetime.datetime | ~datetime.timedelta | PlatformNumber]], _T] | None
            :return:              The result of ``dataclasses.astuple(self) if tuple_factory is None else dataclasses.astuple(self, tuple_factory=tuple_factory)``
            :rtype:              _T | tuple[str, ~datetime.datetime, str, PlatformNumber, ~datetime.timedelta]

Functions
---------

    .. autofunction:: next_services
