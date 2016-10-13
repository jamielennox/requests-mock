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

import cgi
import copy
import json
import sys

import requests
from requests.structures import CaseInsensitiveDict
import six
from six.moves.urllib import parse as urlparse


class _RequestField(object):
    """Mutlipart form encoding accessor.

    When accessing a request from history that had a multipart form body we
    want to provide a way to access parts of that data in a way that looks like
    what we would have provided to requests.
    """

    def __init__(self, data, filename=None, content_type=None, headers=None):
        self.data = data
        self.filename = filename
        self.content_type = content_type
        self.headers = headers or {}

    @classmethod
    def _from_fieldstorage(cls, fs):
        return cls(data=fs.value,
                   filename=fs.filename,
                   headers=CaseInsensitiveDict(fs.headers),
                   content_type=fs.type)

    @property
    def _requests_format(self):
        # This is the order that the parameters are presented to in requests
        # and so we try to provide a similar interface
        return (self.filename, self.data, self.content_type, self.headers)

    def __getitem__(self, item):
        return self._requests_format[item]

    def __len__(self):
        return len(self._requests_format)

    def __iter__(self):
        return iter(self._requests_format)

    def __repr__(self):
        filename = "'%s'" % self.filename if self.filename else 'None'
        c_type = "'%s'" % self.content_type if self.content_type else 'None'
        data = self.data[:48] + '..' if len(self.data) > 50 else self.data
        return "(%s, '%s', %s)" % (filename, data, c_type)

    def __eq__(self, other):
        # if it's a list/tuple treat it like requests does and compare the
        # elements up to as many provided
        if isinstance(other, (list, tuple)):
            if 2 <= len(other) <= 4:
                for i in range(len(other)):
                    if self[i] != other[i]:
                        return False

                return True

        # if it's another _RequestField we should check everything is the same
        if isinstance(other, _RequestField):
            return (self.data == other.data and
                    self.filename == other.filename and
                    self.content_type == other.content_type and
                    self.headers == other.headers)

        # otherwise allow it to just match the data of the form part
        return other == self.data


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

        # FIXME(jamielennox): This is part of bug #1584008 and should default
        # to True (or simply removed) in a major version bump.
        self._case_sensitive = kwargs.pop('case_sensitive', False)

    def __getattr__(self, name):
        return getattr(self._request, name)

    @property
    def _url_parts(self):
        if self._url_parts_ is None:
            url = self._request.url

            if not self._case_sensitive:
                url = url.lower()

            self._url_parts_ = urlparse.urlparse(url)

        return self._url_parts_

    @property
    def scheme(self):
        return self._url_parts.scheme

    @property
    def netloc(self):
        return self._url_parts.netloc

    @property
    def hostname(self):
        try:
            return self.netloc.split(':')[0]
        except IndexError:
            return ''

    @property
    def port(self):
        components = self.netloc.split(':')

        try:
            return int(components[1])
        except (IndexError, ValueError):
            pass

        if self.scheme == 'https':
            return 443
        if self.scheme == 'http':
            return 80

        # The default return shouldn't matter too much because if you are
        # wanting to test this value you really should be explicitly setting it
        # somewhere. 0 at least is a boolean False and an int.
        return 0

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

    @property
    def _input_fp(self):
        return six.BytesIO(self.body)

    @property
    def _environ(self):
        # I'm not sure i'm comfortable making this public. Will re-evaluate if
        # needed but i don't see why anyone else would want it.
        # List: https://www.python.org/dev/peps/pep-0333/#environ-variables
        environ = {
            'REQUEST_METHOD': self.method.upper(),
            'SCRIPT_NAME': '',
            'PATH_INFO': self.path,
            'QUERY_STRING': self.query,
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': self.headers.get('Content-Length',
                                               str(len(self.body))),
            'SERVER_NAME': self.hostname,
            'SERVER_PORT': str(self.port),
            'SERVER_PROTOCOL': self.scheme,
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': self.scheme,
            'wsgi.input': self._input_fp,
            'wsgi.error': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }

        for k, v in self.headers.items():
            environ['HTTP_' + k.replace('-', '_').upper()] = v

        # do cleanup of headers at the end, it's easier
        environ.pop('HTTP_CONTENT_TYPE', None)
        environ.pop('HTTP_CONTENT_LENGTH', None)

        return environ

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

    def form(self, **kwargs):
        kwargs.setdefault('strict_parsing', True)
        return urlparse.parse_qs(self.text, **kwargs)

    def multipart_form(self):
        fs = cgi.FieldStorage(fp=self._input_fp,
                              headers=self.headers,
                              environ=self._environ)

        form = {}

        for name in fs:
            val = fs[name]

            if not isinstance(val, (list, tuple)):
                val = [val]

            form[name] = [_RequestField._from_fieldstorage(f) for f in val]

        return form

    @property
    def matcher(self):
        """The matcher that this request was handled by.

        The matcher object is handled by a weakref. It will return the matcher
        object if it is still available - so if the mock is still in place. If
        the matcher is not available it will return None.
        """
        return self._matcher()
