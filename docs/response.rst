==================
Creating Responses
==================

.. note::

    The examples within use this syntax because response creation is a function of the adapter and not the mocker.
    All the same arguments can be provided to the mocker if that is how you use `requests_mock` within your project, and use the

    .. code:: python

        mock.get(url, ...)

    form in place of the given:

    .. code:: python

        adapter.register_uri('GET', url, ...)

Registering Responses
=====================

Responses are registered with the :py:meth:`requests_mock.Adapter.register_uri` function on the adapter.

.. doctest::

    >>> adapter.register_uri('GET', 'mock://test.com', text='Success')
    >>> resp = session.get('mock://test.com')
    >>> resp.text
    'Success'

:py:meth:`~requests_mock.Adapter.register_uri` takes the HTTP method, the URI and then information that is used to build the response. This information includes:

:status_code: The HTTP status response to return. Defaults to 200.
:reason: The reason text that accompanies the Status (e.g. 'OK' in '200 OK')
:headers: A dictionary of headers to be included in the response.
:cookies: A CookieJar containing all the cookies to add to the response.

To specify the body of the response there are a number of options that depend on the format that you wish to return.

:json: A python object that will be converted to a JSON string.
:text: A unicode string. This is typically what you will want to use for regular textual content.
:content: A byte string. This should be used for including binary data in responses.
:body: A file like object that contains a `.read()` function.
:raw: A prepopulated :py:class:`urllib3.response.HTTPResponse` to be returned.

These options are named to coincide with the parameters on a :py:class:`requests.Response` object. For example:

.. doctest::

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
================

A callback can be provided in place of any of the body elements.
Callbacks must be a function in the form of

.. code:: python

    def callback(request, context):

and return a value suitable to the body element that was specified.
The elements provided are:

:request: The :py:class:`requests.Request` object that was provided.
:context: An object containing the collected known data about this response.

The available properties on the `context` are:

:headers: The dictionary of headers that are to be returned in the response.
:status_code: The status code that is to be returned in the response.
:reason: The string HTTP status code reason that is to be returned in the response.
:cookies: A :py:class:`requests_mock.CookieJar` of cookies that will be merged into the response.

These parameters are populated initially from the variables provided to the :py:meth:`~requests_mock.Adapter.register_uri` function and if they are modified on the context object then those changes will be reflected in the response.

.. doctest::

    >>> def text_callback(request, context):
    ...     context.status_code = 200
    ...     context.headers['Test1'] = 'value1'
    ...     return 'response'
    ...
    >>> adapter.register_uri('GET',
    ...                      'mock://test.com/3',
    ...                      text=text_callback,
    ...                      headers={'Test2': 'value2'},
    ...                      status_code=400)
    >>> resp = session.get('mock://test.com/3')
    >>> resp.status_code, resp.headers, resp.text
    (200, {'Test1': 'value1', 'Test2': 'value2'}, 'response')

Response Lists
==============

Multiple responses can be provided to be returned in order by specifying the keyword parameters in a list.
If the list is exhausted then the last response will continue to be returned.

.. doctest::

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


Callbacks work within response lists in exactly the same way they do normally;

.. doctest::

    >>> adapter.register_uri('GET', 'mock://test.com/5', [{'text': text_callback}]),
    >>> resp = session.get('mock://test.com/5')
    >>> resp.status_code, resp.headers, resp.text
    (200, {'Test1': 'value1', 'Test2': 'value2'}, 'response')

Handling Cookies
================

Whilst cookies are just headers they are treated in a different way, both in HTTP and the requests library.
To work as closely to the requests library as possible there are two ways to provide cookies to requests_mock responses.

The most simple method is to use a dictionary interface.
The Key and value of the dictionary are turned directly into the name and value of the cookie.
This method does not allow you to set any of the more advanced cookie parameters like expiry or domain.

.. doctest::

    >>> adapter.register_uri('GET', 'mock://test.com/6', cookies={'foo': 'bar'}),
    >>> resp = session.get('mock://test.com/6')
    >>> resp.cookies['foo']
    'bar'

The more advanced way is to construct and populate a cookie jar that you can add cookies to and pass that to the mocker.

.. doctest::

    >>> jar = requests_mock.CookieJar()
    >>> jar.set('foo', 'bar', domain='.test.com', path='/baz')
    >>> adapter.register_uri('GET', 'mock://test.com/7', cookies=jar),
    >>> resp = session.get('mock://test.com/7')
    >>> resp.cookies['foo']
    'bar'
    >>> resp.cookies.list_paths()
    ['/baz']
