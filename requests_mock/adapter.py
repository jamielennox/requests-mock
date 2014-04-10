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

import requests
from requests import adapters

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from requests_mock import exceptions


class Matcher(object):

    def __init__(self, url, method, status_code, body, headers):
        self.url = urlparse.urlsplit(url.lower())
        self.method = method
        self.status_code = status_code
        self.body = body.encode('utf-8')
        self.headers = headers

    def create_response(self, request):
        response = requests.Response()
        response.status_code = self.status_code
        response.request = request
        response._content = self.body

        if self.headers:
            response.headers.update(self.headers)

        return response


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


class Adapter(adapters.BaseAdapter):

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

    def register_uri(self, method, url,
                     status_code=200,
                     body='',
                     headers=None):
        self._matchers.append(Matcher(url,
                                      method,
                                      status_code,
                                      body,
                                      headers))

    def latest_request(self):
        """Retrieve the latest request sent"""
        try:
            return self._request_history[-1]
        except IndexError:
            return None


__all__ = ['Adapter']
