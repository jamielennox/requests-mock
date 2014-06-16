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

`requests-mock` provides a building block to stub out the HTTP `requests`_ portions of your testing code.

The Basics
==========

Everything in `requests`_ eventually goes through an adapter to do the transport work.
`requests-mock` creates a custom `adatper` that allows you to predefine responses when certain URIs are called.

There are then a number of methods provided to get the adapter used.

A simple example:

.. code:: python

    >>> import requests
    >>> import requests_mock

    >>> session = requests.Session()
    >>> adapter = requests_mock.Adater()
    >>> session.mount('mock', adapter)

    >>> adapter.register_uri('GET', 'mock://test.com', text='data')
    >>> resp = session.get('mock://test.com')
    >>> resp.status_code, resp.text
    (200, 'data')

Obviously having all URLs be `mock://` prefixed isn't going to useful, so there are a number of ways to get the adapter into place.

For more information checkout the `docs`_.

License
=======

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.

.. _requests: http://python-requests.org
.. _docs: http://requests-mock.readthedocs.org
