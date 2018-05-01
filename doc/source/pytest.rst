======
pytest
======

`pytest`_ has its own method of registering and loading custom fixtures.
*requests-mock* provides an external fixture registered with pytest such that it is usable simply by specifying it as a parameter.
There is no need to import *requests-mock* it simply needs to be installed and specify the argument `requests_mock`.

The fixture then provides the same interface as the :py:class:`requests_mock.Mocker` letting you use *requests-mock* as you would expect.

.. doctest::

    >>> import pytest
    >>> import requests

    >>> def test_url(requests_mock):
    ...     requests_mock.get('http://test.com', text='data')
    ...     assert 'data' == requests.get('http://test.com').text
    ...

.. _pytest: https://pytest.org
