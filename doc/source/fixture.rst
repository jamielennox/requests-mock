========
Fixtures
========

`Fixtures`_ provide a way to create reusable state and helper methods in test cases.

To use the *requests-mock* fixture your tests need to have a dependency on the `fixtures`_ library.
This can be optionally installed when you install *requests-mock* by doing:

.. code:: shell

    pip install requests-mock[fixture]

The fixture mocks the :py:meth:`requests.Session.get_adapter` method so that all requests will be served by the mock adapter.

The fixture provides the same interfaces as the adapter.

.. doctest::

    >>> import requests
    >>> from requests_mock.contrib import fixture
    >>> import testtools

    >>> class MyTestCase(testtools.TestCase):
    ...
    ...     TEST_URL = 'http://www.google.com'
    ...
    ...     def setUp(self):
    ...         super(MyTestCase, self).setUp()
    ...         self.requests_mock = self.useFixture(fixture.Fixture())
    ...         self.requests_mock.register_uri('GET', self.TEST_URL, text='respA')
    ...
    ...     def test_method(self):
    ...         self.requests_mock.register_uri('POST', self.TEST_URL, text='respB')
    ...         resp = requests.get(self.TEST_URL)
    ...         self.assertEqual('respA', resp.text)
    ...         self.assertEqual(self.TEST_URL, self.requests_mock.last_request.url)
    ...


.. _Fixtures: https://pypi.org/project/fixtures/
.. _mock: https://pypi.org/project/mock/
