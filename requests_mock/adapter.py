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


class _Context(object):
    """Stores the data being used to process a current URL match."""

    def __init__(self, request, headers, status_code):
        self.request = request
        self.headers = headers
        self.status_code = status_code

    def call(self, f, *args, **kwargs):
        """Test and call a callback if one was provided.

        If the object provided is callable, then call it and return otherwise
        just return the object.
        """
        if callable(f):
            status_code, headers, data = f(self.request, *args, **kwargs)
            if status_code:
                self.status_code = status_code
            if headers:
                self.headers.update(headers)
            return data
        else:
            return f


class _MatcherResponse(object):

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
        self.status_code = kwargs.pop('status_code', 200)
        self.raw = kwargs.pop('raw', None)
        self.body = kwargs.pop('body', None)
        self.content = kwargs.pop('content', None)
        self.text = kwargs.pop('text', None)
        self.json = kwargs.pop('json', None)
        self.headers = kwargs.pop('headers', {})

        if kwargs:
            raise TypeError('Too many arguments provided to _MatcherResponse')

        # mutual exclusion, only 1 body method may be provided
        provided = sum([bool(x) for x in (self.raw,
                                          self.body,
                                          self.content,
                                          self.text,
                                          self.json)])

        if provided == 0:
            self.body = six.BytesIO(six.b(''))
        elif provided > 1:
            raise RuntimeError('You may only supply one body element')

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
        context = _Context(request, self.headers.copy(), self.status_code)

        content = self.content
        text = self.text
        body = self.body
        raw = self.raw

        if self.json:
            data = context.call(self.json)
            text = jsonutils.dumps(data)
        if text:
            data = context.call(text)
            encoding = 'utf-8'
            content = data.encode(encoding)
        if content:
            data = context.call(content)
            body = six.BytesIO(data)
        if body:
            data = context.call(body)
            raw = HTTPResponse(status=context.status_code,
                               body=data,
                               headers=context.headers,
                               decode_content=False,
                               preload_content=False)

        return encoding, raw


class _Matcher(object):
    """Contains all the information about a provided URL to match."""

    _http_adapter = HTTPAdapter()

    def __init__(self, method, url, responses, complete_qs):
        """
        :param bool complete_qs: Match the entire query string. By default URLs
            match if all the provided matcher query arguments are matched and
            extra query arguments are ignored. Set complete_qs to true to
            require that the entire query string needs to match.
        """
        self.method = method
        self.url = urlparse.urlsplit(url.lower())
        self.responses = responses
        self.complete_qs = complete_qs

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

    def match(self, request):
        if request.method.lower() != self.method.lower():
            return False

        url = urlparse.urlsplit(request.url.lower())

        if self.url.scheme and url.scheme != self.url.scheme:
            return False

        if self.url.netloc and url.netloc != self.url.netloc:
            return False

        if (url.path or '/') != (self.url.path or '/'):
            return False

        matcher_qs = urlparse.parse_qs(self.url.query)
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


class Adapter(BaseAdapter):
    """A fake adapter than can return predefined responses.

    """
    def __init__(self):
        self._matchers = []
        self.request_history = []

    def send(self, request, **kwargs):
        for matcher in self._matchers:
            if matcher.match(request):
                self.request_history.append(request)
                return matcher.create_response(request)

        raise exceptions.NoMockAddress(request)

    def close(self):
        pass

    def register_uri(self, method, url, request_list=None, **kwargs):
        """Register a new URI match and fake response.

        :param str method: The HTTP method to match.
        :param str url: The URL to match.
        """
        complete_qs = kwargs.pop('complete_qs', False)

        if request_list and kwargs:
            raise RuntimeError('You should specify either a list of '
                               'responses OR response kwargs. Not both.')
        elif not request_list:
            request_list = [kwargs]

        responses = [_MatcherResponse(**k) for k in request_list]
        self._matchers.append(_Matcher(method,
                                       url,
                                       responses,
                                       complete_qs=complete_qs))

    @property
    def last_request(self):
        """Retrieve the latest request sent"""
        try:
            return self.request_history[-1]
        except IndexError:
            return None


__all__ = ['Adapter']
