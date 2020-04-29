===============
Request History
===============

The object returned from creating a mock or registering a URI in an adapter is capable of tracking and querying the history of requests that this mock responded to.

Called
======

The easiest way to test if a request hit the adapter is to simply check the called property or the call_count property.

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

The alias `last_request` is also available for the last request to go through the mocker.

This request object is a wrapper around a standard :py:class:`requests.Request` object with some additional information that make the interface more workable (as the :py:class:`~requests.Request` object is generally not dealt with by users.

These additions include:

:text: The data of the request converted into a unicode string.
:json: The data of the request loaded from json into python objects.
:qs: The query string of the request. See :py:func:`urllib.parse.parse_qs` for information on the return format.
:hostname: The host name that the request was sent to.
:port: The port the request was sent to.

.. doctest::

    >>> m.last_request.scheme
    'http'
    >>> m.last_request.netloc
    'test.com'

The following parameters of the :py:func:`requests.request` call are also exposed via the request object:

:timeout: How long to wait for the server to send data before giving up.
:allow_redirects: Set to True if POST/PUT/DELETE redirect following is allowed.
:proxies: Dictionary mapping protocol to the URL of the proxy.
:verify: whether the SSL cert will be verified.
:cert: The client certificate or cert/key tuple for this request.

Note: That the default value of these attributes are the values that are passed to the adapter and not what is passed to the request method. This means that the default for allow_redirects is None (even though that is interpretted as True) if unset, whereas the defautl for verify is True, and the default for proxies the empty dict.

Reset History
===============

For mocks, adapters, and matchers, the history can be reset. This can be useful when testing complex code with multiple requests. 

For mocks, use "reset_mock" method.

.. doctest::

    >>> m.called
    True
    >>> m.reset_mock()
    >>> m.called
    False
    >>> m.call_count
    0

For adapters and matchers, there is a "reset" method. Resetting the adapter also resets the associated matchers.

.. doctest::

    >>> adapter = requests_mock.adapter.Adapter()
    >>> matcher = adapter.register_uri('GET', 'mock://test.com', text='resp')
    >>> session = requests.Session()
    >>> session.mount('mock://', adapter)
    >>> session.get('mock://test.com')
    >>> adapter.called
    True
    >>> adapter.reset()
    >>> adapter.called
    False
    >>> matcher.called  # Reset adapter also resets associated matchers
    False

However, resetting the matcher does not reset the adapter.

.. doctest::

    >>> session.get('mock://test.com')
    >>> matcher.called
    True
    >>> matcher.reset()
    >>> matcher.called
    False
    >>> adapter.called  # Reset matcher does not reset adapter
    True
