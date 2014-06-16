===============================
requests-mock
===============================

.. image:: https://badge.fury.io/py/requests-mock.png
    :target: http://badge.fury.io/py/requests-mock

.. image:: https://travis-ci.org/jamielennox/requests-mock.png?branch=master
        :target: https://travis-ci.org/jamielennox/requests-mock

.. image:: https://pypip.in/d/requests-mock/badge.png
        :target: https://crate.io/packages/requests-mock?version=latest

.. image:: https://coveralls.io/repos/jamielennox/requests-mock/badge.png
        :target: https://coveralls.io/r/jamielennox/requests-mock

Intro
=====

`requests-mock` provides a simple way to stub out the HTTP portions or your testing code.


What is it
==========

The `requests`_ library has the concept of `pluggable transport adapters`_.
These adapters allow you to register your own handlers for different URIs or protocols.

The *requests-mock* library at its core is simply a transport adapter that can be preloaded with responses that are returned if certain URIs are requested.
This is particularly useful in unit tests where you want to return known responses from HTTP requests without making actual calls.

As the `requests`_ library has very limited options for how to load and use adapters *requests-mock* also provides a number (currently 1) of ways that to make sure the mock adapter is used.
These are only loading mechanisms, they do not contain any logic and can be used as a reference to load the adapter in whatever ways works best for your project.

Adapter Usage
=============

Creating an Adapter
-------------------

The standard `requests`_ means of using an adapter is to mount it on a created session. This is not the only way to load the adapter, however the same interactions will be used.

.. code:: python

    >>> import requests
    >>> import requests_mock

    >>> session = requests.Session()
    >>> adapter = requests_mock.Adapter()
    >>> session.mount('mock', adapter)

At this point any requests made by the session to a URI starting with `mock://` will be sent to our adapter.


Registering Responses
---------------------

Responses are registered with the `register_uri` function on the adapter.

.. code:: python

    >>> adapter.register_uri('GET', 'mock://test.com', text='Success')
    >>> resp = session.get('mock://test.com')
    >>> resp.text
    'Success'

`register_uri` takes the HTTP method, the URI and then information that is used to build the response. This information includes:

:status_code: The HTTP status response to return. Defaults to 200.
:reason: The reason text that accompanies the Status (e.g. 'OK' in '200 OK')
:headers: A dictionary of headers to be included in the response.

To specify the body of the response there are a number of options that depend on the format that you wish to return.

:json: A python object that will be converted to a JSON string.
:text: A unicode string. This is typically what you will want to use for regular textual content.
:content: A byte string. This should be used for including binary data in responses.
:body: A file like object that contains a `.read()` function.
:raw: A prepopulated urllib3 response to be returned.

These options are named to coincide with the parameters on a `requests.Response` object. For example:

.. code:: python

    >>> adapter.register_uri('GET', 'mock://test.com/1', json={'a': 'b'}, status_code=200)
    >>> resp = session.get('mock://test.com/1')
    >>> resp.json()
    {'a': 'b'}

    >>> adapter.register_uri('GET', 'mock://test.com/2', text='Not Found', status_code=404)
    >>> resp = session.get('mock://test.com/2')
    >>> resp.text
    'Not Found'
    >>> resp.status_code
    404

It only makes sense to provide at most one body element per response.

Dynamic Response
----------------

A callback can be provided in place of any of the body elements.
Callbacks must be a function in the form of

.. code:: python

    def callback(request, context):

and return a value suitable to the body element that was specified.
The elements provided are:

:request: The `requests.Request` object that was provided.
:context: An object containing the collected known data about this response.

The available properties on the `context` are:

:headers: The dictionary of headers that are to be returned in the response.
:status_code: The status code that is to be returned in the response.
:reason: The string HTTP status code reason that is to be returned in the response.

These parameters are populated initially from the variables provided to the `register_uri` function and if they are modified on the context object then those changes will be reflected in the response.

.. code:: python

    >>> def text_callback(request, context):
    ...     context.status_code = 200
    ...     context.headers['Test1'] = 'value1'
    ...     return 'response'
    ...
    >>> adapter.register_uri('GET', 'mock://test.com/3', text=text_callback, headers={'Test2': 'value2'}, status_code=400)
    >>> resp = session.get('mock://test.com/3')
    >>> resp.status_code, resp.headers, resp.text
    (200, {'Test1': 'value1', 'Test2': 'value2'}, 'response')

Response Lists
--------------

Multiple responses can be provided to be returned in order by specifying the keyword parameters in a list.
If the list is exhausted then the last response will continue to be returned.

.. code:: python

    >>> adapter.register_uri('GET', 'mock://test.com/4', [{'text': 'resp1', 'status_code': 300},
    ...                                                   {'text': 'resp2', 'status_code': 200}])
    >>> resp = session.get('mock://test.com/4')
    >>> (resp.status_code, resp.text)
    (300, 'resp1')
    >>> resp = session.get('mock://test.com/4')
    >>> (resp.status_code, resp.text)
    (200, 'resp2')
    >>> resp = session.get('mock://test.com/4')
    >>> (resp.status_code, resp.text)
    (200, 'resp2')


Request Matching
================

Whilst it is preferable to provide the whole URI to `register_uri` it is possible to just specify components.

You can specify a protocol-less path:

.. code:: python

    >>> adapter.register_uri('GET', '//test.com/5', text='resp')
    >>> session.get('mock://test.com/5').text
    'resp'

or you can specify just a path:

.. code:: python

    >>> adapter.register_uri('GET', '/6', text='resp')
    >>> session.get('mock://test.com/6').text
    'resp'
    >>> session.get('mock://another.com/6').text
    'resp'

Query strings provided to a register will match so long as at least those provided form part of the request.

.. code:: python

    >>> adapter.register_uri('GET', '/7?a=1', text='resp')
    >>> session.get('mock://test.com/7?a=1&b=2').text
    'resp'

    >>> session.get('mock://test.com/7?a=3')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: GET mock://test.com/7?a=3

This can be a problem in certain situations, so if you wish to match only the complete query string there is a flag `complete_qs`:

.. code:: python

    >>> adapter.register_uri('GET', '/8?a=1', complete_qs=True, text='resp')
    >>> session.get('mock://test.com/8?a=1&b=2')
    Traceback (most recent call last):
       ...
    requests_mock.exceptions.NoMockAddress: No mock address: GET mock://test.com/8?a=1&b=2

.. _requests: http://python-requests.org
.. _pluggable transport adapters: http://docs.python-requests.org/en/latest/user/advanced/#transport-adapters


