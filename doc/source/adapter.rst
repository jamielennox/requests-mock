=============
Adapter Usage
=============

Creating an Adapter
===================

The standard `requests`_ means of using an adapter is to :py:meth:`~requests.Session.mount` it on a created session. This is not the only way to load the adapter, however the same interactions will be used.

.. doctest::

    >>> import requests
    >>> import requests_mock

    >>> session = requests.Session()
    >>> adapter = requests_mock.Adapter()
    >>> session.mount('mock', adapter)

At this point any requests made by the session to a URI starting with `mock://` will be sent to our adapter.

.. _requests: http://python-requests.org
