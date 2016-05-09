# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy
import json
import weakref

import requests
from requests.adapters import BaseAdapter
import six
from six.moves.urllib import parse as urlparse

from requests_mock import exceptions
from requests_mock import response

ANY = object()


class _RequestObjectProxy(object):
    """A wrapper around a requests.Request that gives some extra information.

    This will be important both for matching and so that when it's save into
    the request_history users will be able to access these properties.
    """

    def __init__(self, request, **kwargs):
        self._request = request
        self._matcher = None
        self._url_parts_ = None
        self._qs = None

        # All of these params should always exist but we use a default
        # to make the test setup easier.
        self._timeout = kwargs.pop('timeout', None)
        self._allow_redirects = kwargs.pop('allow_redirects', None)
        self._verify = kwargs.pop('verify', None)
        self._cert = kwargs.pop('cert', None)
        self._proxies = copy.deepcopy(kwargs.pop('proxies', {}))

    def __getattr__(self, name):
        return getattr(self._request, name)

    @property
    def _url_parts(self):
        if self._url_parts_ is None:
            self._url_parts_ = urlparse.urlparse(self._request.url.lower())

        return self._url_parts_

    @property
    def scheme(self):
        return self._url_parts.scheme

    @property
    def netloc(self):
        return self._url_parts.netloc

    @property
    def path(self):
        return self._url_parts.path

    @property
    def query(self):
        return self._url_parts.query

    @property
    def qs(self):
        if self._qs is None:
            self._qs = urlparse.parse_qs(self.query)

        return self._qs

    @property
    def timeout(self):
        return self._timeout

    @property
    def allow_redirects(self):
        return self._allow_redirects

    @property
    def verify(self):
        return self._verify

    @property
    def cert(self):
        return self._cert

    @property
    def proxies(self):
        return self._proxies

    @classmethod
    def _create(cls, *args, **kwargs):
        return cls(requests.Request(*args, **kwargs).prepare())

    @property
    def text(self):
        body = self.body

        if isinstance(body, six.binary_type):
            body = body.decode('utf-8')

        return body

    def json(self, **kwargs):
        return json.loads(self.text, **kwargs)

    @property
    def matcher(self):
        """The matcher that this request was handled by.

        The matcher object is handled by a weakref. It will return the matcher
        object if it is still available - so if the mock is still in place. If
        the matcher is not available it will return None.
        """
        return self._matcher()


class _RequestHistoryTracker(object):

    def __init__(self):
        self.request_history = []

    def _add_to_history(self, request):
        self.request_history.append(request)

    @property
    def last_request(self):
        """Retrieve the latest request sent"""
        try:
            return self.request_history[-1]
        except IndexError:
            return None

    @property
    def called(self):
        return self.call_count > 0

    @property
    def call_count(self):
        return len(self.request_history)


class _Matcher(_RequestHistoryTracker):
    """Contains all the information about a provided URL to match."""

    def __init__(self, method, url, responses, complete_qs, request_headers):
        """
        :param bool complete_qs: Match the entire query string. By default URLs
            match if all the provided matcher query arguments are matched and
            extra query arguments are ignored. Set complete_qs to true to
            require that the entire query string needs to match.
        """
        super(_Matcher, self).__init__()
        self._method = method
        self._url = url
        try:
            self._url_parts = urlparse.urlparse(url.lower())
        except:
            self._url_parts = None
        self._responses = responses
        self._complete_qs = complete_qs
        self._request_headers = request_headers

    def _match_method(self, request):
        if self._method is ANY:
            return True

        if request.method.lower() == self._method.lower():
            return True

        return False

    def _match_url(self, request):
        if self._url is ANY:
            return True

        # regular expression matching
        if hasattr(self._url, 'search'):
            return self._url.search(request.url) is not None

        if self._url_parts.scheme and request.scheme != self._url_parts.scheme:
            return False

        if self._url_parts.netloc and request.netloc != self._url_parts.netloc:
            return False

        if (request.path or '/') != (self._url_parts.path or '/'):
            return False

        # construct our own qs structure as we remove items from it below
        request_qs = urlparse.parse_qs(request.query)
        matcher_qs = urlparse.parse_qs(self._url_parts.query)

        for k, vals in six.iteritems(matcher_qs):
            for v in vals:
                try:
                    request_qs.get(k, []).remove(v)
                except ValueError:
                    return False

        if self._complete_qs:
            for v in six.itervalues(request_qs):
                if v:
                    return False

        return True

    def _match_headers(self, request):
        for k, vals in six.iteritems(self._request_headers):

            try:
                header = request.headers[k]
            except KeyError:
                # NOTE(jamielennox): This seems to be a requests 1.2/2
                # difference, in 2 they are just whatever the user inputted in
                # 1 they are bytes. Let's optionally handle both and look at
                # removing this when we depend on requests 2.
                if not isinstance(k, six.text_type):
                    return False

                try:
                    header = request.headers[k.encode('utf-8')]
                except KeyError:
                    return False

            if header != vals:
                return False

        return True

    def _match(self, request):
        return (self._match_method(request) and
                self._match_url(request) and
                self._match_headers(request))

    def __call__(self, request):
        if not self._match(request):
            return None

        if len(self._responses) > 1:
            response_matcher = self._responses.pop(0)
        else:
            response_matcher = self._responses[0]

        self._add_to_history(request)
        return response_matcher.get_response(request)


class Adapter(BaseAdapter, _RequestHistoryTracker):
    """A fake adapter than can return predefined responses.

    """
    def __init__(self):
        super(Adapter, self).__init__()
        self._matchers = []

    def send(self, request, **kwargs):
        request = _RequestObjectProxy(request, **kwargs)
        self._add_to_history(request)

        for matcher in reversed(self._matchers):
            try:
                resp = matcher(request)
            except Exception:
                request._matcher = weakref.ref(matcher)
                raise

            if resp is not None:
                request._matcher = weakref.ref(matcher)
                resp.connection = self
                return resp

        raise exceptions.NoMockAddress(request)

    def close(self):
        pass

    def register_uri(self, method, url, response_list=None, **kwargs):
        """Register a new URI match and fake response.

        :param str method: The HTTP method to match.
        :param str url: The URL to match.
        """
        complete_qs = kwargs.pop('complete_qs', False)
        request_headers = kwargs.pop('request_headers', {})

        if response_list and kwargs:
            raise RuntimeError('You should specify either a list of '
                               'responses OR response kwargs. Not both.')
        elif not response_list:
            response_list = [kwargs]

        responses = [response._MatcherResponse(**k) for k in response_list]
        matcher = _Matcher(method,
                           url,
                           responses,
                           complete_qs=complete_qs,
                           request_headers=request_headers)
        self.add_matcher(matcher)
        return matcher

    def add_matcher(self, matcher):
        """Register a custom matcher.

        A matcher is a callable that takes a `requests.Request` and returns a
        `requests.Response` if it matches or None if not.

        :param callable matcher: The matcher to execute.
        """
        self._matchers.append(matcher)


__all__ = ['Adapter']
