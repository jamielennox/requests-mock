================
Using the Mocker
================

The mocker is a loading mechanism to ensure the adapter is correctly in place to intercept calls from requests.
It's goal is to provide an interface that is as close to the real requests library interface as possible.

Activation
==========

Loading of the Adapter is handled by the :py:class:`requests_mock.Mocker` class, which provides two ways to load an adapter:

Context Manager
---------------

The Mocker object can work as a context manager.

.. doctest::

    >>> import requests
    >>> import requests_mock

    >>> with requests_mock.Mocker() as m:
    ...     m.get('http://test.com', text='resp')
    ...     requests.get('http://test.com').text
    ...
    'resp'

Decorator
---------

Mocker can also be used as a decorator. The created object will then be passed as the last positional argument.

.. doctest::

    >>> @requests_mock.Mocker()
    ... def test_function(m):
    ...     m.get('http://test.com', text='resp')
    ...     return requests.get('http://test.com').text
    ...
    >>> test_function()
    'resp'

If the position of the mock is likely to conflict with other arguments you can pass the `kw` argument to the Mocker to have the mocker object passed as that keyword argument instead.

.. doctest::

    >>> @requests_mock.Mocker(kw='mock')
    ... def test_kw_function(**kwargs):
    ...     kwargs['mock'].get('http://test.com', text='resp')
    ...     return requests.get('http://test.com').text
    ...
    >>> test_kw_function()
    'resp'

Class Decorator
===============

Mocker can also be used to decorate a whole class. It works exactly like in case of decorating a normal function.
When used in this way they wrap every test method on the class. The mocker recognise methods that start with *test* as being test methods.
This is the same way that the `unittest.TestLoader` finds test methods by default.
It is possible that you want to use a different prefix for your tests. You can inform the mocker of the different prefix by setting `requests_mock.Mocker.TEST_PREFIX`:

.. doctest::

    >>> requests_mock.Mocker.TEST_PREFIX = 'foo'
    >>>
    >>> @requests_mock.Mocker()
    ... class Thing(object):
    ...     def foo_one(self, m):
    ...        m.register_uri('GET', 'http://test.com', text='resp')
    ...        return requests.get('http://test.com').text
    ...     def foo_two(self, m):
    ...         m.register_uri('GET', 'http://test.com', text='resp')
    ...         return requests.get('http://test.com').text
    ...
    >>>
    >>> Thing().foo_one()
    'resp'
    >>> Thing().foo_two()
    'resp'


This behavior mimics how patchers from `mock` library works.


Methods
=======

The mocker object can be used with a similar interface to requests itself.

.. doctest::

    >>> with requests_mock.Mocker() as mock:
    ...     mock.get('http://test.com', text='resp')
    ...     requests.get('http://test.com').text
    ...
    'resp'


The functions exist for the common HTTP method:

  - :py:meth:`~requests_mock.MockerCore.delete`
  - :py:meth:`~requests_mock.MockerCore.get`
  - :py:meth:`~requests_mock.MockerCore.head`
  - :py:meth:`~requests_mock.MockerCore.options`
  - :py:meth:`~requests_mock.MockerCore.patch`
  - :py:meth:`~requests_mock.MockerCore.post`
  - :py:meth:`~requests_mock.MockerCore.put`

As well as the basic:

  - :py:meth:`~requests_mock.MockerCore.request`
  - :py:meth:`~requests_mock.MockerCore.register_uri`

These methods correspond to the HTTP method of your request, so to mock POST requests you would use the :py:meth:`~requests_mock.MockerCore.post` function.
Futher information about what can be matched from a request can be found at :doc:`matching`

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
