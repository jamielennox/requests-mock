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

import re

import requests
import six

from requests_mock import adapter
from requests_mock.tests import base

ANY = adapter.ANY


class SessionAdapterTests(base.TestCase):

    PREFIX = "mock"

    def setUp(self):
        super(SessionAdapterTests, self).setUp()

        self.adapter = adapter.Adapter()
        self.session = requests.Session()
        self.session.mount(self.PREFIX, self.adapter)

        self.url = '%s://example.com/test' % self.PREFIX
        self.headers = {'header_a': 'A', 'header_b': 'B'}

    def assertHeaders(self, resp):
        for k, v in six.iteritems(self.headers):
            self.assertEqual(v, resp.headers[k])

    def assertLastRequest(self, method='GET', body=None):
        self.assertEqual(self.url, self.adapter.last_request.url)
        self.assertEqual(method, self.adapter.last_request.method)
        self.assertEqual(body, self.adapter.last_request.body)

    def test_content(self):
        data = six.b('testdata')

        self.adapter.register_uri('GET',
                                  self.url,
                                  content=data,
                                  headers=self.headers)
        resp = self.session.get(self.url)
        self.assertEqual(data, resp.content)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_content_callback(self):
        status_code = 401
        data = six.b('testdata')

        def _content_cb(request, context):
            context.status_code = status_code
            context.headers.update(self.headers)
            return data

        self.adapter.register_uri('GET',
                                  self.url,
                                  content=_content_cb)
        resp = self.session.get(self.url)
        self.assertEqual(status_code, resp.status_code)
        self.assertEqual(data, resp.content)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_text(self):
        data = 'testdata'

        self.adapter.register_uri('GET',
                                  self.url,
                                  text=data,
                                  headers=self.headers)
        resp = self.session.get(self.url)
        self.assertEqual(six.b(data), resp.content)
        self.assertEqual(six.u(data), resp.text)
        self.assertEqual('utf-8', resp.encoding)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_text_callback(self):
        status_code = 401
        data = 'testdata'

        def _text_cb(request, context):
            context.status_code = status_code
            context.headers.update(self.headers)
            return six.u(data)

        self.adapter.register_uri('GET', self.url, text=_text_cb)
        resp = self.session.get(self.url)
        self.assertEqual(status_code, resp.status_code)
        self.assertEqual(six.u(data), resp.text)
        self.assertEqual(six.b(data), resp.content)
        self.assertEqual('utf-8', resp.encoding)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_json(self):
        json_data = {'hello': 'world'}
        self.adapter.register_uri('GET',
                                  self.url,
                                  json=json_data,
                                  headers=self.headers)
        resp = self.session.get(self.url)
        self.assertEqual(six.b('{"hello": "world"}'), resp.content)
        self.assertEqual(six.u('{"hello": "world"}'), resp.text)
        self.assertEqual(json_data, resp.json())
        self.assertEqual('utf-8', resp.encoding)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_json_callback(self):
        status_code = 401
        json_data = {'hello': 'world'}
        data = '{"hello": "world"}'

        def _json_cb(request, context):
            context.status_code = status_code
            context.headers.update(self.headers)
            return json_data

        self.adapter.register_uri('GET', self.url, json=_json_cb)
        resp = self.session.get(self.url)
        self.assertEqual(status_code, resp.status_code)
        self.assertEqual(json_data, resp.json())
        self.assertEqual(six.u(data), resp.text)
        self.assertEqual(six.b(data), resp.content)
        self.assertEqual('utf-8', resp.encoding)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_no_body(self):
        self.adapter.register_uri('GET', self.url)
        resp = self.session.get(self.url)
        self.assertEqual(six.b(''), resp.content)
        self.assertEqual(200, resp.status_code)

    def test_multiple_body_elements(self):
        self.assertRaises(RuntimeError,
                          self.adapter.register_uri,
                          self.url,
                          'GET',
                          content=six.b('b'),
                          text=six.u('u'))

    def test_multiple_responses(self):
        inp = [{'status_code': 400, 'text': 'abcd'},
               {'status_code': 300, 'text': 'defg'},
               {'status_code': 200, 'text': 'hijk'}]

        self.adapter.register_uri('GET', self.url, inp)
        out = [self.session.get(self.url) for i in range(0, len(inp))]

        for i, o in zip(inp, out):
            for k, v in six.iteritems(i):
                self.assertEqual(v, getattr(o, k))

        last = self.session.get(self.url)
        for k, v in six.iteritems(inp[-1]):
            self.assertEqual(v, getattr(last, k))

    def test_callback_optional_status(self):
        headers = {'a': 'b'}

        def _test_cb(request, context):
            context.headers.update(headers)
            return ''

        self.adapter.register_uri('GET',
                                  self.url,
                                  text=_test_cb,
                                  status_code=300)
        resp = self.session.get(self.url)
        self.assertEqual(300, resp.status_code)

        for k, v in six.iteritems(headers):
            self.assertEqual(v, resp.headers[k])

    def test_callback_optional_headers(self):
        headers = {'a': 'b'}

        def _test_cb(request, context):
            context.status_code = 300
            return ''

        self.adapter.register_uri('GET',
                                  self.url,
                                  text=_test_cb,
                                  headers=headers)

        resp = self.session.get(self.url)
        self.assertEqual(300, resp.status_code)

        for k, v in six.iteritems(headers):
            self.assertEqual(v, resp.headers[k])

    def test_latest_register_overrides(self):
        self.adapter.register_uri('GET', self.url, text='abc')
        self.adapter.register_uri('GET', self.url, text='def')

        resp = self.session.get(self.url)
        self.assertEqual('def', resp.text)

    def test_no_last_request(self):
        self.assertIsNone(self.adapter.last_request)
        self.assertEqual(0, len(self.adapter.request_history))

    def test_dont_pass_list_and_kwargs(self):
        self.assertRaises(RuntimeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          [{'text': 'a'}],
                          headers={'a': 'b'})

    def test_empty_string_return(self):
        # '' evaluates as False, so make sure an empty string is not ignored.
        self.adapter.register_uri('GET', self.url, text='')
        resp = self.session.get(self.url)
        self.assertEqual('', resp.text)

    def test_dont_pass_multiple_bodies(self):
        self.assertRaises(RuntimeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          json={'abc': 'def'},
                          text='ghi')

    def test_dont_pass_unexpected_kwargs(self):
        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          unknown='argument')

    def test_dont_pass_unicode_as_content(self):
        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          content=six.u('unicode'))

    def test_dont_pass_bytes_as_text(self):
        if six.PY2:
            self.skipTest('Cannot enforce byte behaviour in PY2')

        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          text=six.b('bytes'))

    def test_dont_pass_non_str_as_content(self):
        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          content=5)

    def test_dont_pass_non_str_as_text(self):
        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          text=5)

    def test_with_any_method(self):
        self.adapter.register_uri(ANY, self.url, text='resp')

        for m in ('GET', 'HEAD', 'POST', 'UNKNOWN'):
            resp = self.session.request(m, self.url)
            self.assertEqual('resp', resp.text)

    def test_with_any_url(self):
        self.adapter.register_uri('GET', ANY, text='resp')

        for u in ('mock://a', 'mock://b', 'mock://c'):
            resp = self.session.get(u)
            self.assertEqual('resp', resp.text)

    def test_with_regexp(self):
        self.adapter.register_uri('GET', re.compile('tester.com'), text='resp')

        for u in ('mocK://www.tester.com/a', 'mock://abc.tester.com'):
            resp = self.session.get(u)
            self.assertEqual('resp', resp.text)
