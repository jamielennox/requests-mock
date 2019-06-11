============
Known Issues
============

.. _case_insensitive:

Case Insensitivity
------------------

By default matching is done in a completely case insensitive way. This makes
sense for the protocol and host components which are defined as insensitive by
RFCs however it does not make sense for path.

A byproduct of this is that when using request history the values for path, qs
etc are all lowercased as this was what was used to do the matching.

To work around this when building an Adapter or Mocker you do

.. code:: python

    with requests_mock.mock(case_sensitive=True) as m:
       ...

or you can override the default globally by

.. code:: python

    requests_mock.mock.case_sensitive = True

It is recommended to run the global fix as it is intended that case sensitivity
will become the default in future releases.

Note that even with case_sensitive enabled the protocol and netloc of a mock
are still matched in a case insensitive way.

Cookies in Sessions
-------------------

If a mocked response sets a cookie, the cookie will be accessible through the
Response object as expected.

If, however, the mocked response is requested through a Session, the cookie will
not reach the Session instance.

The problem is that the Requests library adds cookies to Session objects by
reading the ``httplib`` response object, not the ``requests`` Response object.
Mock responses naturally don't use ``httplib``.

To fix this issue, the *requests-mock* library needs to convert all acceptable
forms of mocked cookies into ``Set-Cookie`` headers to enable the Requests
library to properly process them.

This issue is being tracked on GitHub:

https://github.com/jamielennox/requests-mock/issues/17
