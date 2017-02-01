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
from requests_mock import exceptions
from requests_mock import response
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
        test_text = 'real http data'
        test_bytes = test_text.encode('utf-8')

        # using create_response is a bit bootstrappy here but so long as it's
        # coming from HTTPAdapter.send it's ok
        req = requests.Request(method='GET', url=url)
        real_send.return_value = response.create_response(req.prepare(),
                                                          status_code=200,
                                                          content=test_bytes)
        resp = requests.get(url)

        self.assertEqual(1, real_send.call_count)
        self.assertEqual(url, real_send.call_args[0][0].url)

        self.assertEqual(test_text, resp.text)
        self.assertEqual(test_bytes, resp.content)

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
        self.assertTrue(matcher.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

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
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_get(self, m):
        mock_obj = m.get(self.URL, text=self.TEXT)
        self.assertResponse(requests.get(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_options(self, m):
        mock_obj = m.options(self.URL, text=self.TEXT)
        self.assertResponse(requests.options(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_head(self, m):
        mock_obj = m.head(self.URL, text=self.TEXT)
        self.assertResponse(requests.head(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_post(self, m):
        mock_obj = m.post(self.URL, text=self.TEXT)
        self.assertResponse(requests.post(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_put(self, m):
        mock_obj = m.put(self.URL, text=self.TEXT)
        self.assertResponse(requests.put(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_patch(self, m):
        mock_obj = m.patch(self.URL, text=self.TEXT)
        self.assertResponse(requests.patch(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_delete(self, m):
        mock_obj = m.delete(self.URL, text=self.TEXT)
        self.assertResponse(requests.delete(self.URL))
        self.assertTrue(mock_obj.called)
        self.assertTrue(mock_obj.called_once)
        self.assertTrue(m.called)
        self.assertTrue(m.called_once)

    @requests_mock.Mocker()
    def test_mocker_real_http_and_responses(self, m):
        self.assertRaises(RuntimeError,
                          m.get,
                          self.URL,
                          text='abcd',
                          real_http=True)

    @requests_mock.Mocker()
    def test_mocker_real_http(self, m):
        data = 'testdata'

        uri1 = 'fake://example.com/foo'
        uri2 = 'fake://example.com/bar'
        uri3 = 'fake://example.com/baz'

        m.get(uri1, text=data)
        m.get(uri2, real_http=True)

        self.assertEqual(data, requests.get(uri1).text)

        # This should fail because requests can't get an adapter for mock://
        # but it shows that it has tried and would have made a request.
        self.assertRaises(requests.exceptions.InvalidSchema,
                          requests.get,
                          uri2)

        # This fails because real_http is not set on the mocker
        self.assertRaises(exceptions.NoMockAddress,
                          requests.get,
                          uri3)

        # do it again to make sure the mock is still in place
        self.assertEqual(data, requests.get(uri1).text)

    @requests_mock.Mocker(case_sensitive=True)
    def test_case_sensitive_query(self, m):
        data = 'testdata'
        query = {'aBcDe': 'FgHiJ'}

        m.get(self.URL, text=data)
        resp = requests.get(self.URL, params=query)

        self.assertEqual('GET', m.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)

        for k, v in query.items():
            self.assertEqual([v], m.last_request.qs[k])

    @mock.patch.object(requests_mock.Mocker, 'case_sensitive', True)
    def test_global_case_sensitive(self):
        with requests_mock.mock() as m:
            data = 'testdata'
            query = {'aBcDe': 'FgHiJ'}

            m.get(self.URL, text=data)
            resp = requests.get(self.URL, params=query)

            self.assertEqual('GET', m.last_request.method)
            self.assertEqual(200, resp.status_code)
            self.assertEqual(data, resp.text)

            for k, v in query.items():
                self.assertEqual([v], m.last_request.qs[k])

    def test_nested_mocking(self):
        url1 = 'http://url1.com/path1'
        url2 = 'http://url2.com/path2'
        url3 = 'http://url3.com/path3'

        data1 = 'data1'
        data2 = 'data2'
        data3 = 'data3'

        with requests_mock.mock() as m1:

            r1 = m1.get(url1, text=data1)

            resp1a = requests.get(url1)
            self.assertRaises(exceptions.NoMockAddress, requests.get, url2)
            self.assertRaises(exceptions.NoMockAddress, requests.get, url3)

            self.assertEqual(data1, resp1a.text)

            # call count = 3 because there are 3 calls above, url 1-3
            self.assertEqual(3, m1.call_count)
            self.assertEqual(1, r1.call_count)

            with requests_mock.mock() as m2:

                r2 = m2.get(url2, text=data2)

                self.assertRaises(exceptions.NoMockAddress, requests.get, url1)
                resp2a = requests.get(url2)
                self.assertRaises(exceptions.NoMockAddress, requests.get, url3)

                self.assertEqual(data2, resp2a.text)

                with requests_mock.mock() as m3:

                    r3 = m3.get(url3, text=data3)

                    self.assertRaises(exceptions.NoMockAddress,
                                      requests.get,
                                      url1)
                    self.assertRaises(exceptions.NoMockAddress,
                                      requests.get,
                                      url2)
                    resp3 = requests.get(url3)

                    self.assertEqual(data3, resp3.text)

                    self.assertEqual(3, m3.call_count)
                    self.assertEqual(1, r3.call_count)

                resp2b = requests.get(url2)
                self.assertRaises(exceptions.NoMockAddress, requests.get, url1)
                self.assertEqual(data2, resp2b.text)
                self.assertRaises(exceptions.NoMockAddress, requests.get, url3)

                self.assertEqual(3, m1.call_count)
                self.assertEqual(1, r1.call_count)
                self.assertEqual(6, m2.call_count)
                self.assertEqual(2, r2.call_count)
                self.assertEqual(3, m3.call_count)
                self.assertEqual(1, r3.call_count)

            resp1b = requests.get(url1)
            self.assertEqual(data1, resp1b.text)
            self.assertRaises(exceptions.NoMockAddress, requests.get, url2)
            self.assertRaises(exceptions.NoMockAddress, requests.get, url3)

            self.assertEqual(6, m1.call_count)
            self.assertEqual(2, r1.call_count)

    @requests_mock.mock()
    def test_mocker_additional(self, m):
        url = 'http://www.example.com'
        good_text = 'success'

        def additional_cb(req):
            return 'hello' in req.text

        m.post(url, additional_matcher=additional_cb, text=good_text)

        self.assertEqual(good_text,
                         requests.post(url, data='hello world').text)
        self.assertRaises(exceptions.NoMockAddress,
                          requests.post,
                          url,
                          data='goodbye world')
