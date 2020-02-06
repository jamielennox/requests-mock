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

If you are unfamiliar with how pytest decorators work then please `read the fixture documentation` first as it means that you should no longer use the `@requests_mock.Mocker` syntax that is present in the documentation examples.
This confusion between how `unittest`_ and `pytest`_ work is the biggest source of complaint and is not a `requests-mock` inherent problem.

.. _pytest: https://pytest.org
.. _unittest: https://docs.python.org/3/library/unittest.html
.. _read the fixture documentation: https://docs.pytest.org/en/latest/fixture.html

Configuration
=============

Some options are available to be read from pytest's configuration mechanism.

These options are:

   `requests_mock_case_sensitive`: (bool) Turn on case sensitivity in path matching.

Background
==========

This section was initially copied from `StackOverflow`_

`pytest`_ doesn't play along with function decorators that add positional arguments to the test function.
`pytest`_ considers all arguments that:

- aren't bound to an instance or type as in instance or class methods;
- don't have default values;
- aren't bound with functools.partial;
- aren't replaced with unittest.mock mocks

to be replaced with fixture values, and will fail if it doesn't find a suitable fixture for any argument. So stuff like

.. code-block:: python

    import functools
    import pytest


    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args += ('spam',)
            return func(*args, **kwargs)
        return wrapper


    @deco
    def test_spam(spam_arg):
        assert True

will fail, and this is exactly what requests-mock does. A workaround to that would be passing the mocker via keyword args:

.. code-block:: python

    import pytest
    import requests_mock


    @requests_mock.Mocker(kw='m')
    def test_with_mock_and_fixtures(capsys, **kwargs):
        m = kwargs['m']
        ...

however at this point it would simply be easier to use the provided pytest decorator.

.. _stackoverflow: https://stackoverflow.com/a/52065289/544047
