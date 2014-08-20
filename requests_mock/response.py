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

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.response import HTTPResponse
import six

from requests_mock import compat
from requests_mock import exceptions

_BODY_ARGS = frozenset(['raw', 'body', 'content', 'text', 'json'])
_HTTP_ARGS = frozenset(['status_code', 'reason', 'headers'])

_DEFAULT_STATUS = 200
_http_adapter = HTTPAdapter()


def _check_body_arguments(**kwargs):
    # mutual exclusion, only 1 body method may be provided
    provided = [x for x in _BODY_ARGS if kwargs.pop(x, None) is not None]

    if len(provided) > 1:
        raise RuntimeError('You may only supply one body element. You '
                           'supplied %s' % ', '.join(provided))

    extra = [x for x in kwargs if x not in _HTTP_ARGS]

    if extra:
        raise TypeError('Too many arguments provided. Unexpected '
                        'arguments %s.' % ', '.join(extra))


class _FakeConnection(object):
    """An object that can mock the necessary parts of a socket interface."""

    def send(self, request, **kwargs):
        msg = 'This response was created without a connection. You are ' \
              'therefore unable to make a request directly on that connection.'
        raise exceptions.InvalidRequest(msg)

    def close(self):
        pass


def create_response(request, **kwargs):
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
    connection = kwargs.pop('connection', _FakeConnection())

    _check_body_arguments(**kwargs)

    raw = kwargs.pop('raw', None)
    body = kwargs.pop('body', None)
    content = kwargs.pop('content', None)
    text = kwargs.pop('text', None)
    json = kwargs.pop('json', None)
    encoding = None

    if content and not isinstance(content, six.binary_type):
        raise TypeError('Content should be a callback or binary data')
    if text and not isinstance(text, six.string_types):
        raise TypeError('Text should be a callback or string data')

    if json is not None:
        text = jsonutils.dumps(json)
    if text is not None:
        encoding = 'utf-8'
        content = text.encode(encoding)
    if content is not None:
        body = six.BytesIO(content)
    if not raw:
        raw = HTTPResponse(status=kwargs.get('status_code', _DEFAULT_STATUS),
                           headers=kwargs.get('headers', {}),
                           reason=kwargs.get('reason'),
                           body=body or six.BytesIO(six.b('')),
                           decode_content=False,
                           preload_content=False,
                           original_response=compat._fake_http_response)

    response = _http_adapter.build_response(request, raw)
    response.connection = connection
    response.encoding = encoding
    return response


class _Context(object):
    """Stores the data being used to process a current URL match."""

    def __init__(self, headers, status_code, reason):
        self.headers = headers
        self.status_code = status_code
        self.reason = reason


class _MatcherResponse(object):

    def __init__(self, **kwargs):
        _check_body_arguments(**kwargs)
        self._params = kwargs

        # whilst in general you shouldn't do type checking in python this
        # makes sure we don't end up with differences between the way types
        # are handled between python 2 and 3.
        content = self._params.get('content')
        text = self._params.get('text')

        if content and not (callable(content) or
                            isinstance(content, six.binary_type)):
            raise TypeError('Content should be a callback or binary data')

        if text and not (callable(text) or
                         isinstance(text, six.string_types)):
            raise TypeError('Text should be a callback or string data')

    def get_response(self, request):
        context = _Context(self._params.get('headers', {}).copy(),
                           self._params.get('status_code', _DEFAULT_STATUS),
                           self._params.get('reason'))

        # if a body element is a callback then execute it
        def _call(f, *args, **kwargs):
            return f(request, context, *args, **kwargs) if callable(f) else f

        return create_response(request,
                               json=_call(self._params.get('json')),
                               text=_call(self._params.get('text')),
                               content=_call(self._params.get('content')),
                               body=_call(self._params.get('body')),
                               raw=self._params.get('raw'),
                               status_code=context.status_code,
                               reason=context.reason,
                               headers=context.headers)
