================
Request Matching
================

Whilst it is preferable to provide the whole URI to :py:meth:`requests_mock.Adapter.register_uri` it is possible to just specify components.

The examples in this file are loaded with:

.. doctest::

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

.. note::

    The examples within use this syntax because request matching is a function of the adapter and not the mocker.
    All the same arguments can be provided to the mocker if that is how you use `requests_mock` within your project, and use the

    .. code:: python

        mock.get(url, ...)

    form in place of the given:

    .. code:: python

        adapter.register_uri('GET', url, ...)

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

Simple
======

The most simple way to match a request is to register the URL and method that will be requested with a textual response.
When a request is made that goes through the mocker this response will be retrieved.

.. doctest::

    .. >>> adapter.register_uri('GET', 'mock://test.com/path', text='resp')
    .. >>> session.get('mock://test.com/path').text
    .. 'resp'

Path Matching
=============


You can specify a protocol-less path:

.. doctest::

    .. >>> adapter.register_uri('GET', '//test.com/', text='resp')
    .. >>> session.get('mock://test.com/').text
    .. 'resp'

or you can specify just a path:

.. doctest::

    .. >>> adapter.register_uri('GET', '/path', text='resp')
    .. >>> session.get('mock://test.com/path').text
    .. 'resp'
    .. >>> session.get('mock://another.com/path').text
    .. 'resp'

Query Strings
=============

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

Query strings provided to a register will match so long as at least those provided form part of the request.

.. doctest::

    >>> adapter.register_uri('GET', '/7?a=1', text='resp')
    >>> session.get('mock://test.com/7?a=1&b=2').text
    'resp'

If any part of the query string is wrong then it will not match.

.. doctest::

    >>> session.get('mock://test.com/7?a=3')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: GET mock://test.com/7?a=3

This can be a problem in certain situations, so if you wish to match only the complete query string there is a flag `complete_qs`:

.. doctest::

    >>> adapter.register_uri('GET', '/8?a=1', complete_qs=True, text='resp')
    >>> session.get('mock://test.com/8?a=1&b=2')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: GET mock://test.com/8?a=1&b=2


Matching ANY
============

There is a special symbol at `requests_mock.ANY` which acts as the wildcard to match anything.
It can be used as a replace for the method and/or the URL.

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

.. doctest::

    >>> adapter.register_uri(requests_mock.ANY, 'mock://test.com/8', text='resp')
    >>> session.get('mock://test.com/8').text
    'resp'
    >>> session.post('mock://test.com/8').text
    'resp'

.. doctest::

    >>> adapter.register_uri(requests_mock.ANY, requests_mock.ANY, text='resp')
    >>> session.get('mock://whatever/you/like').text
    'resp'
    >>> session.post('mock://whatever/you/like').text
    'resp'

Regular Expressions
===================

URLs can be specified with a regular expression using the python :py:mod:`re` module.
To use this you should pass an object created by :py:func:`re.compile`.

The URL is then matched using :py:meth:`re.regex.search` which means that it will match any component of the url, so if you want to match the start of a URL you will have to anchor it.

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

.. doctest::

    .. >>> import re
    .. >>> matcher = re.compile('tester.com/a')
    .. >>> adapter.register_uri('GET', matcher, text='resp')
    .. >>> session.get('mock://www.tester.com/a/b').text
    .. 'resp'

If you use regular expression matching then *requests-mock* can't do it's normal query string or path only matching, that will need to be part of the expression.


Request Headers
===============

A dictionary of headers can be supplied such that the request will only match if the available headers also match.
Only the headers that are provided need match, any additional headers will be ignored.

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

.. doctest::

    >>> adapter.register_uri('POST', 'mock://test.com/headers', request_headers={'key': 'val'}, text='resp')
    >>> session.post('mock://test.com/headers', headers={'key': 'val', 'another': 'header'}).text
    'resp'
    >>> resp = session.post('mock://test.com/headers')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: POST mock://test.com/headers


Custom Matching
===============

Internally calling :py:meth:`~requests_mock.Adapter.register_uri` creates a *matcher* object for you and adds it to the list of matchers to check against.

A *matcher* is any callable that takes a :py:class:`requests.Request` and returns a :py:class:`requests.Response` on a successful match or *None* if it does not handle the request.

If you need more flexibility than provided by :py:meth:`~requests_mock.Adapter.register_uri` then you can add your own *matcher* to the :py:class:`~requests_mock.Adapter`. Custom *matchers* can be used in conjunction with the inbuilt *matchers*. If a matcher returns *None* then the request will be passed to the next *matcher* as with using :py:meth:`~requests_mock.Adapter.register_uri`.

.. doctest::
    :hide:

    >>> import requests
    >>> import requests_mock
    >>> adapter = requests_mock.Adapter()
    >>> session = requests.Session()
    >>> session.mount('mock', adapter)

.. doctest::

    >>> def custom_matcher(request):
    ...     if request.path_url == '/test':
    ...         resp = requests.Response()
    ...         resp.status_code = 200
    ...         return resp
    ...     return None
    ...
    >>> adapter.add_matcher(custom_matcher)
    >>> session.get('mock://test.com/test').status_code
    200
    >>> session.get('mock://test.com/other')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: POST mock://test.com/other
