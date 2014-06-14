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
import six

from requests_mock import adapter
from requests_mock.tests import base


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
        last = self.adapter.last_request()
        self.assertEqual(self.url, last.url)
        self.assertEqual(method, last.method)
        self.assertEqual(body, last.body)

    def test_content(self):
        data = 'testdata'

        self.adapter.register_uri('GET',
                                  self.url,
                                  content=data,
                                  headers=self.headers)
        resp = self.session.get(self.url)
        self.assertEqual(six.b(data), resp.content)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_content_callback(self):
        status_code = 401
        data = six.b('testdata')

        def _content_cb(request):
            return status_code, self.headers, data

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

        def _text_cb(request):
            return status_code, self.headers, six.u(data)

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

        def _json_cb(request):
            return status_code, self.headers, json_data

        self.adapter.register_uri('GET', self.url, json=_json_cb)
        resp = self.session.get(self.url)
        self.assertEqual(status_code, resp.status_code)
        self.assertEqual(json_data, resp.json())
        self.assertEqual(six.u(data), resp.text)
        self.assertEqual(six.b(data), resp.content)
        self.assertEqual('utf-8', resp.encoding)
        self.assertHeaders(resp)
        self.assertLastRequest()

    def test_multiple_body_elements(self):
        self.assertRaises(RuntimeError,
                          self.adapter.register_uri,
                          self.url,
                          'GET',
                          content=six.b('b'),
                          text=six.u('u'))
