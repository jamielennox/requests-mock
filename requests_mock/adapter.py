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
from six import BytesIO
from six.moves.urllib import parse as urlparse

from requests_mock import exceptions


class Context(object):

    def __init__(self, request, headers, status_code):
        self.request = request
        self.headers = headers.copy()
        self.status_code = status_code

    def call(self, f, *args, **kwargs):
        if callable(f):
            status_code, headers, data = f(self.request, *args, **kwargs)
            if status_code:
                self.status_code = status_code
            if headers:
                self.headers.update(headers)
            return data
        else:
            return f


class Matcher(object):

    _http_adapter = HTTPAdapter()

    def __init__(self,
                 method,
                 url,
                 status_code=200,
                 raw=None,
                 body=None,
                 content=None,
                 text=None,
                 json=None,
                 headers=None):
        self.method = method
        self.url = urlparse.urlsplit(url.lower())
        self.status_code = status_code
        self.raw = raw
        self.body = body
        self.content = content
        self.text = text
        self.json = json
        self.headers = headers or {}

        if sum([bool(x) for x in (self.raw,
                                  self.body,
                                  self.content,
                                  self.text,
                                  self.json)]) > 1:
            raise RuntimeError('You may only supply one body element')

    def _get_response(self, request):
        encoding = None
        context = Context(request, self.headers, self.status_code)

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
            body = BytesIO(data)
        if body:
            data = context.call(body)
            raw = HTTPResponse(status=context.status_code,
                               body=data,
                               headers=context.headers,
                               decode_content=False,
                               preload_content=False)

        return encoding, raw

    def create_response(self, request):
        encoding, response = self._get_response(request)
        req_resp = self._http_adapter.build_response(request, response)
        req_resp.connection = self
        req_resp.encoding = encoding
        return req_resp

    def close(self):
        pass


def match(request, matcher):
    if request.method.lower() != matcher.method.lower():
        return False

    url = urlparse.urlsplit(request.url.lower())

    if matcher.url.scheme and url.scheme != matcher.url.scheme:
        return False

    if matcher.url.netloc and url.netloc != matcher.url.netloc:
        return False

    if matcher.url.path and url.path != matcher.url.path:
        return False

    return True


class Adapter(BaseAdapter):

    def __init__(self):
        self._matchers = []
        self._request_history = []

    def send(self, request, **kwargs):
        self._request_history.append(request)

        for matcher in self._matchers:
            if match(request, matcher):
                return matcher.create_response(request)

        raise exceptions.NoMockAddress(request)

    def close(self):
        pass

    def register_uri(self, *args, **kwargs):
        self._matchers.append(Matcher(*args, **kwargs))

    def last_request(self):
        """Retrieve the latest request sent"""
        try:
            return self._request_history[-1]
        except IndexError:
            return None


__all__ = ['Adapter']
