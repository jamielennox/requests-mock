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
-----

`requests-mock` provides a simple way to stub out the HTTP portions or your testing code.


Usage
-----

The only means of using `requests-mock` at the moment is in conjunction with the fixtures library.

.. code:: python

    import requests
    import requests_mock
    import testtools

    class MyTestCase(testtools.TestCase):

        def setUp(self):
            super(MyTestCase, self).setUp()
            self.requests_mock = self.useFixture(requests_mock.Mock())

        def test_case(self):
            self.requests_mock.register_uri('GET', 'http://www.google.com',
                                            body='Success')

            resp = requests.get('http://www.google.com')

            self.assertEqual('Success', resp.text)

TODO
----

* Fixtures shouldn't be the only way of stubbing, should allow a context manager and a decorator.
* Should allow stubbing an individual session object rather than the entire library.
