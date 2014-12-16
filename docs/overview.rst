========
Overview
========

The `requests`_ library has the concept of `pluggable transport adapters`_.
These adapters allow you to register your own handlers for different URIs or protocols.

The *requests-mock* library at its core is simply a transport adapter that can be preloaded with responses that are returned if certain URIs are requested.
This is particularly useful in unit tests where you want to return known responses from HTTP requests without making actual calls.

As the `requests`_ library has very limited options for how to load and use adapters *requests-mock* also provides a number of ways to make sure the mock adapter is used.
These are only loading mechanisms, they do not contain any logic and can be used as a reference to load the adapter in whatever ways works best for your project.

.. _requests: http://python-requests.org
.. _pluggable transport adapters: http://docs.python-requests.org/en/latest/user/advanced/#transport-adapters
