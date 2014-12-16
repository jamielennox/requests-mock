===============
Request History
===============

The object returned from creating a mock or registering a URI in an adapter is capable of tracking and querying the history of requests that this mock responded to.

Called
======

The easiest way to test if a request hit the adapter is to simply check the called property.

.. doctest::

    >>> import requests
    >>> import requests_mock

    >>> with requests_mock.mock() as m:
    ...     m.get('http://test.com, text='resp')
    ...     resp = requests.get('http://test.com')
    ...
    >>> m.called
    True
    >>> m.call_count
    1

Request Objects
===============

The history of objects that passed through the `mocker`/`adapter` can also be retrieved

.. doctest::

    >>> history = m.request_history
    >>> len(history)
    1
    >>> history[0].method
    'GET'
    >>> history[0].url
    'http://test.com/'

This request history object is a wrapper around a standard :py:class:`requests.Request` object with some additional information that make the interface more workable (as the :py:class:`~requests.Request` object is generally not dealt with by users.

These additions include:

:text: The data of the request converted into a unicode string.
:json: The data of the request loaded from json into python objects.
:qs: The query string of the request. See :py:meth:`urllib.parse.parse_qs` for information on the return format.
