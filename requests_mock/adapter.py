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

import json as jsonutils

from requests.adapters import BaseAdapter, HTTPAdapter
from requests.packages.urllib3.response import HTTPResponse
import six
from six.moves.urllib import parse as urlparse

from requests_mock import exceptions

ANY = object()


class _Context(object):
    """Stores the data being used to process a current URL match."""

    def __init__(self, headers, status_code, reason):
        self.headers = headers
        self.status_code = status_code
        self.reason = reason


class _MatcherResponse(object):

    _BODY_ARGS = ['raw', 'body', 'content', 'text', 'json']

    def __init__(self, **kwargs):
        """
        :param int status_code: The status code to return upon a successful
            match. Defaults to 200.
        :param HTTPResponse raw: A HTTPResponse object to return upon a
            successful match.
        :param io.IOBase body: An IO object with a read() method that can
            return a body on successful match.
        :param bytes content: A byte string to return upon a successful match.
        :param unicode text: A text string to return upon a successful match.
        :param object json: A python object to be converted to a JSON string
            and returned upon a successful match.
        :param dict headers: A dictionary object containing headers that are
            returned upon a successful match.
        """
        # mutual exclusion, only 1 body method may be provided
        provided = [x for x in self._BODY_ARGS if kwargs.get(x) is not None]

        self.status_code = kwargs.pop('status_code', 200)
        self.raw = kwargs.pop('raw', None)
        self.body = kwargs.pop('body', None)
        self.content = kwargs.pop('content', None)
        self.text = kwargs.pop('text', None)
        self.json = kwargs.pop('json', None)
        self.reason = kwargs.pop('reason', None)
        self.headers = kwargs.pop('headers', {})

        if kwargs:
            raise TypeError('Too many arguments provided. Unexpected '
                            'arguments %s' % ', '.join(kwargs.keys()))

        if len(provided) == 0:
            self.body = six.BytesIO(six.b(''))
        elif len(provided) > 1:
            raise RuntimeError('You may only supply one body element. You '
                               'supplied %s' % ', '.join(provided))

        # whilst in general you shouldn't do type checking in python this
        # makes sure we don't end up with differences between the way types
        # are handled between python 2 and 3.
        if self.content and not (callable(self.content) or
                                 isinstance(self.content, six.binary_type)):
            raise TypeError('Content should be a callback or binary data')
        if self.text and not (callable(self.text) or
                              isinstance(self.text, six.string_types)):
            raise TypeError('Text should be a callback or string data')

    def get_response(self, request):
        encoding = None
        context = _Context(self.headers.copy(),
                           self.status_code,
                           self.reason)

        # if a body element is a callback then execute it
        def _call(f, *args, **kwargs):
            return f(request, context, *args, **kwargs) if callable(f) else f

        content = self.content
        text = self.text
        body = self.body
        raw = self.raw

        if self.json is not None:
            data = _call(self.json)
            text = jsonutils.dumps(data)
        if text is not None:
            data = _call(text)
            encoding = 'utf-8'
            content = data.encode(encoding)
        if content is not None:
            data = _call(content)
            body = six.BytesIO(data)
        if body is not None:
            data = _call(body)
            raw = HTTPResponse(status=context.status_code,
                               body=data,
                               headers=context.headers,
                               reason=context.reason,
                               decode_content=False,
                               preload_content=False)

        return encoding, raw


class _Matcher(object):
    """Contains all the information about a provided URL to match."""

    _http_adapter = HTTPAdapter()

    def __init__(self, method, url, responses, complete_qs, request_headers):
        """
        :param bool complete_qs: Match the entire query string. By default URLs
            match if all the provided matcher query arguments are matched and
            extra query arguments are ignored. Set complete_qs to true to
            require that the entire query string needs to match.
        """
        self.method = method
        self.url = url
        try:
            self.url_parts = urlparse.urlparse(url.lower())
        except:
            self.url_parts = None
        self.responses = responses
        self.complete_qs = complete_qs
        self.request_headers = request_headers

    def create_response(self, request):
        if len(self.responses) > 1:
            response_matcher = self.responses.pop(0)
        else:
            response_matcher = self.responses[0]

        encoding, response = response_matcher.get_response(request)
        req_resp = self._http_adapter.build_response(request, response)
        req_resp.connection = self
        req_resp.encoding = encoding
        return req_resp

    def close(self):
        pass

    def _match_method(self, request):
        if self.method is ANY:
            return True

        if request.method.lower() == self.method.lower():
            return True

        return False

    def _match_url(self, request):
        if self.url is ANY:
            return True

        # regular expression matching
        if hasattr(self.url, 'search'):
            return self.url.search(request.url) is not None

        url = urlparse.urlparse(request.url.lower())

        if self.url_parts.scheme and url.scheme != self.url_parts.scheme:
            return False

        if self.url_parts.netloc and url.netloc != self.url_parts.netloc:
            return False

        if (url.path or '/') != (self.url_parts.path or '/'):
            return False

        matcher_qs = urlparse.parse_qs(self.url_parts.query)
        request_qs = urlparse.parse_qs(url.query)

        for k, vals in six.iteritems(matcher_qs):
            for v in vals:
                try:
                    request_qs.get(k, []).remove(v)
                except ValueError:
                    return False

        if self.complete_qs:
            for v in six.itervalues(request_qs):
                if v:
                    return False

        return True

    def _match_headers(self, request):
        for k, vals in six.iteritems(self.request_headers):
            try:
                header = request.headers[k]
            except KeyError:
                return False
            else:
                if header != vals:
                    return False

        return True

    def match(self, request):
        return (self._match_method(request) and
                self._match_url(request) and
                self._match_headers(request))

    def __call__(self, request):
        if self.match(request):
            return self.create_response(request)


class Adapter(BaseAdapter):
    """A fake adapter than can return predefined responses.

    """
    def __init__(self):
        super(Adapter, self).__init__()
        self._matchers = []
        self.request_history = []

    def send(self, request, **kwargs):
        for matcher in reversed(self._matchers):
            response = matcher(request)
            if response is not None:
                self.request_history.append(request)
                return response

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

        responses = [_MatcherResponse(**k) for k in response_list]
        self.add_matcher(_Matcher(method,
                                  url,
                                  responses,
                                  complete_qs=complete_qs,
                                  request_headers=request_headers))

    def add_matcher(self, matcher):
        """Register a custom matcher.

        A matcher is a callable that takes a `requests.Request` and returns a
        `requests.Response` if it matches or None if not.

        :param callable matcher: The matcher to execute.
        """
        self._matchers.append(matcher)

    @property
    def last_request(self):
        """Retrieve the latest request sent"""
        try:
            return self.request_history[-1]
        except IndexError:
            return None


__all__ = ['Adapter']
