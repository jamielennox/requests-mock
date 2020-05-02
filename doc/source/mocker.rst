.. _Mocker:

================
Using the Mocker
================

The mocker is a loading mechanism to ensure the adapter is correctly in place to intercept calls from requests.
Its goal is to provide an interface that is as close to the real requests library interface as possible.

:py:class:`requests_mock.Mocker` takes two optional parameters:

:real_http (bool): If True then any requests that are not handled by the mocking adapter will be forwarded to the real server (see :ref:`RealHTTP`), or the containing Mocker if applicable (see :ref:`NestingMockers`). Defaults to False.
:session (requests.Session): If set, only the given session instance is mocked (see :ref:`SessionMocking`).

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

Contrib
-------

The contrib module also provides ways of loading the mocker based on other frameworks.
These will require additional dependencies but may provide a better experience depending on your tests setup.

See :doc:`contrib` for these additions.


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
Further information about what can be matched from a request can be found at :doc:`matching`

.. _RealHTTP:

Real HTTP Requests
==================

If :py:data:`real_http` is set to :py:const:`True`
then any requests that are not handled by the mocking adapter will be forwarded to the real server,
or the containing Mocker if applicable (see :ref:`NestingMockers`).

.. doctest::

    >>> with requests_mock.Mocker(real_http=True) as m:
    ...     m.register_uri('GET', 'http://test.com', text='resp')
    ...     print(requests.get('http://test.com').text)
    ...     print(requests.get('http://www.google.com').status_code)  # doctest: +SKIP
    ...
    'resp'
    200

*New in 1.1*

Similarly when using a mocker you can register an individual URI to bypass the mocking infrastructure and make a real request. Note this only works when using the mocker and not when directly mounting an adapter.

.. doctest::

    >>> with requests_mock.Mocker() as m:
    ...     m.register_uri('GET', 'http://test.com', text='resp')
    ...     m.register_uri('GET', 'http://www.google.com', real_http=True)
    ...     print(requests.get('http://test.com').text)
    ...     print(requests.get('http://www.google.com').status_code)  # doctest: +SKIP
    ...
    'resp'
    200

.. _NestingMockers:

Nested Mockers
==============

*New in 1.8*

When nesting mockers the innermost Mocker replaces all others.
If :py:data:`real_http` is set to :py:const:`True`, at creation or for a given resource,
the request is passed to the containing Mocker.
The containing Mocker can in turn:

- serve the request;
- raise :py:exc:`NoMockAddress`;
- or pass the request to yet another Mocker (or to the unmocked :py:class:`requests.Session`) if :py:data:`real_http` is set to :py:const:`True`.

.. doctest::

    >>> url = "https://www.example.com/"
    >>> with requests_mock.Mocker() as outer_mock:
    ...     outer_mock.get(url, text='outer')
    ...     with requests_mock.Mocker(real_http=True) as middle_mock:
    ...         with requests_mock.Mocker() as inner_mock:
    ...             inner_mock.get(url, real_http=True)
    ...             print(requests.get(url).text)  # doctest: +SKIP
    ...
    'outer'

Most of the time nesting can be avoided by making the mocker object available to subclasses/subfunctions.

.. warning::
   When starting/stopping mockers manually, make sure to stop innermost mockers first.
   A call from an active inner mocker with a stopped outer mocker leads to undefined behavior.

.. _SessionMocking:

Mocking specific sessions
=========================

*New in 1.8*

:py:class:`requests_mock.Mocker` can be used to mock specific sessions through the :py:data:`session` parameter.

.. doctest::

    >>> url = "https://www.example.com/"
    >>> with requests_mock.Mocker() as global_mock:
    ...     global_mock.get(url, text='global')
    ...     session = requests.Session()
    ...     print("requests.get before session mock:", requests.get(url).text)
    ...     print("session.get before session mock:", session.get(url).text)
    ...     with requests_mock.Mocker(session=session) as session_mock:
    ...         session_mock.get(url, text='session')
    ...         print("Within session mock:", requests.get(url).text)
    ...         print("Within session mock:", session.get(url).text)
    ...     print("After session mock:", requests.get(url).text)
    ...     print("After session mock:", session.get(url).text)
    ...
    'requests.get before session mock: global'
    'session.get before session mock: global'
    'requests.get within session mock: global'
    'session.get within session mock: session'
    'requests.get after session mock: global'
    'session.get after session mock: global'



.. note::
  As an alternative, :py:class:`requests_mock.Adapter` instances can be mounted on specific sessions (see :ref:`Adapter`).
