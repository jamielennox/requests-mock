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

import mock
import requests

import requests_mock
from requests_mock.tests import base

original_send = requests.Session.send


class MockerTests(base.TestCase):

    def assertMockStarted(self):
        self.assertNotEqual(original_send, requests.Session.send)

    def assertMockStopped(self):
        self.assertEqual(original_send, requests.Session.send)

    def _do_test(self, m):
        self.assertMockStarted()
        m.register_uri('GET', 'http://www.test.com', text='resp')
        resp = requests.get('http://www.test.com')
        self.assertEqual('resp', resp.text)

    def test_multiple_starts(self):
        mocker = requests_mock.Mocker()
        self.assertMockStopped()
        mocker.start()
        self.assertMockStarted()
        self.assertRaises(RuntimeError, mocker.start)
        mocker.stop()
        self.assertMockStopped()
        mocker.stop()

    def test_with_context_manager(self):
        self.assertMockStopped()
        with requests_mock.Mocker() as m:
            self._do_test(m)
        self.assertMockStopped()

    @mock.patch('requests.adapters.HTTPAdapter.send')
    @requests_mock.mock(real_http=True)
    def test_real_http(self, real_send, mocker):
        url = 'http://www.google.com/'

        real_send.return_value = requests.Response()
        real_send.return_value.status_code = 200
        requests.get(url)

        self.assertEqual(1, real_send.call_count)
        self.assertEqual(url, real_send.call_args[0][0].url)

    @requests_mock.mock()
    def test_with_test_decorator(self, m):
        self._do_test(m)

    @requests_mock.mock(kw='mock')
    def test_with_mocker_kwargs(self, **kwargs):
        self._do_test(kwargs['mock'])

    def test_with_decorator(self):

        @requests_mock.mock()
        def inner(m):
            self.assertMockStarted()
            self._do_test(m)

        self.assertMockStopped()
        inner()
        self.assertMockStopped()

    @requests_mock.mock()
    def test_query_string(self, m):
        url = 'http://test.url/path'
        qs = 'a=1&b=2'
        m.register_uri('GET', url, text='resp')
        resp = requests.get("%s?%s" % (url, qs))

        self.assertEqual('resp', resp.text)

        self.assertEqual(qs, m.last_request.query)
        self.assertEqual(['1'], m.last_request.qs['a'])
        self.assertEqual(['2'], m.last_request.qs['b'])


class MockerHttpMethodsTests(base.TestCase):

    URL = 'http://test.com/path'
    TEXT = 'resp'

    def assertResponse(self, resp):
        self.assertEqual(self.TEXT, resp.text)

    @requests_mock.Mocker()
    def test_mocker_request(self, m):
        method = 'XXX'
        mock_obj = m.request(method, self.URL, text=self.TEXT)
        resp = requests.request(method, self.URL)
        self.assertResponse(resp)
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_get(self, m):
        mock_obj = m.get(self.URL, text=self.TEXT)
        self.assertResponse(requests.get(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_options(self, m):
        mock_obj = m.options(self.URL, text=self.TEXT)
        self.assertResponse(requests.options(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_head(self, m):
        mock_obj = m.head(self.URL, text=self.TEXT)
        self.assertResponse(requests.head(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_post(self, m):
        mock_obj = m.post(self.URL, text=self.TEXT)
        self.assertResponse(requests.post(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_put(self, m):
        mock_obj = m.put(self.URL, text=self.TEXT)
        self.assertResponse(requests.put(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_patch(self, m):
        mock_obj = m.patch(self.URL, text=self.TEXT)
        self.assertResponse(requests.patch(self.URL))
        self.assertTrue(mock_obj.called)

    @requests_mock.Mocker()
    def test_mocker_delete(self, m):
        mock_obj = m.delete(self.URL, text=self.TEXT)
        self.assertResponse(requests.delete(self.URL))
        self.assertTrue(mock_obj.called)
