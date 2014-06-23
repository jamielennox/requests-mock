==============
Mocker Loading
==============

Loading of the Adapter is handled by the :py:class:`requests_mock.Mocker` class, which provides two ways to load an adapter.

Context Manager
===============

The Mocker object can work as a context manager.

.. doctest::

    >>> import requests
    >>> import requests_mock

    >>> with requests_mock.Mocker() as m:
    ...     m.register_uri('GET', 'http://test.com', text='resp')
    ...     requests.get('http://test.com').text
    ...
    'resp'

Decorator
=========

Mocker can also be used as a decorator. The created object will then be passed as the last positional argument.

.. doctest::

    >>> @requests_mock.Mocker()
    ... def test_function(m):
    ...     m.register_uri('GET', 'http://test.com', text='resp')
    ...     return requests.get('http://test.com').text
    ...
    >>> test_function()
    'resp'

If the position of the mock is likely to conflict with other arguments you can pass the `kw` argument to the Mocker to have the mocker object passed as that keyword argument instead.

.. doctest::

    >>> @requests_mock.Mocker(kw='mock')
    ... def test_kw_function(**kwargs):
    ...     kwargs['mock'].register_uri('GET', 'http://test.com', text='resp')
    ...     return requests.get('http://test.com').text
    ...
    >>> test_kw_function()
    'resp'

Real HTTP Requests
==================

The Mocker object takes the following parameters:

:real_http (bool): If True then any requests that are not handled by the mocking adapter will be forwarded to the real server. Defaults to False.

.. doctest::

    >>> with requests_mock.Mocker(real_http=True) as m:
    ...     m.register_uri('GET', 'http://test.com', text='resp')
    ...     print(requests.get('http://test.com').text)
    ...     print(requests.get('http://www.google.com').status_code)  # doctest: +SKIP
    ...
    'resp'
    200
