================
Request Matching
================

Whilst it is preferable to provide the whole URI to :py:meth:`requests_mock.Adapter.register_uri` it is possible to just specify components.

Basic
=====

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


Query Strings
=============

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


Matching ANY
============

There is a special symbol at `requests_mock.ANY` which acts as the wildcard to match anything.
It can be used as a replace for the method and/or the URL.

.. code:: python

    >>> adapter.register_uri(requests_mock.ANY, 'mock://test.com/8', text='resp')
    >>> session.get('mock://test.com/8').text
    'resp'
    >>> session.post('mock://test.com/8').text
    'resp'

.. code:: python

    >>> adapter.register_uri(requests_mock.ANY, requests_mock.ANY, text='resp')
    >>> session.get('mock://whatever/you/like')
    'resp'
    >>> session.post('mock://whatever/you/like')
    'resp'
