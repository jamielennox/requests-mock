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
from requests_mock import compat
from requests_mock.tests import base

original_send = requests.Session.send


class MockerTests(base.TestCase):

    def assertMockStarted(self):
        self.assertNotEqual(original_send, requests.Session.send)

    def assertMockStopped(self):
        self.assertEqual(original_send, requests.Session.send)

    def _do_test(self, m):
        self.assertMockStarted()
        matcher = m.register_uri('GET', 'http://www.test.com', text='resp')
        resp = requests.get('http://www.test.com')
        self.assertEqual('resp', resp.text)
        return matcher

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

        # NOTE(jamielennox): hack for requests 1.2.3 remove after
        # requirements catches up.
        class FakeHTTPResponse(object):
            _original_response = compat._fake_http_response

        real_send.return_value = requests.Response()
        real_send.return_value.status_code = 200
        real_send.return_value.raw = FakeHTTPResponse()
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

    def test_with_class_decorator(self):
        outer = self

        @requests_mock.mock()
        class Decorated(object):

            def test_will_be_decorated(self, m):
                outer.assertMockStarted()
                outer._do_test(m)

            def will_not_be_decorated(self):
                outer.assertMockStopped()

        decorated_class = Decorated()

        self.assertMockStopped()
        decorated_class.test_will_be_decorated()
        self.assertMockStopped()
        decorated_class.will_not_be_decorated()
        self.assertMockStopped()

    def test_with_class_decorator_and_custom_kw(self):
        outer = self

        @requests_mock.mock(kw='custom_m')
        class Decorated(object):

            def test_will_be_decorated(self, **kwargs):
                outer.assertMockStarted()
                outer._do_test(kwargs['custom_m'])

            def will_not_be_decorated(self):
                outer.assertMockStopped()

        decorated_class = Decorated()

        self.assertMockStopped()
        decorated_class.test_will_be_decorated()
        self.assertMockStopped()
        decorated_class.will_not_be_decorated()
        self.assertMockStopped()

    @mock.patch.object(requests_mock.mock, 'TEST_PREFIX', 'foo')
    def test_with_class_decorator_and_custom_test_prefix(self):
        outer = self

        @requests_mock.mock()
        class Decorated(object):

            def foo_will_be_decorated(self, m):
                outer.assertMockStarted()
                outer._do_test(m)

            def will_not_be_decorated(self):
                outer.assertMockStopped()

        decorated_class = Decorated()

        self.assertMockStopped()
        decorated_class.foo_will_be_decorated()
        self.assertMockStopped()
        decorated_class.will_not_be_decorated()
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

    @requests_mock.mock()
    def test_mock_matcher_attributes(self, m):
        matcher = self._do_test(m)

        self.assertEqual(1, matcher.call_count)
        self.assertEqual(1, m.call_count)

        self.assertTrue(matcher.called)
        self.assertTrue(m.called)

        self.assertEqual(m.request_history, matcher.request_history)
        self.assertIs(m.last_request, matcher.last_request)

    def test_copy(self):
        mocker = requests_mock.mock(kw='foo', real_http=True)
        copy_of_mocker = mocker.copy()
        self.assertIsNot(copy_of_mocker, mocker)
        self.assertEqual(copy_of_mocker._kw, mocker._kw)
        self.assertEqual(copy_of_mocker._real_http, mocker._real_http)


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
