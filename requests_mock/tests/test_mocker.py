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
    @requests_mock.Mocker(real_http=True)
    def test_real_http(self, real_send, mocker):
        url = 'http://www.google.com/'

        real_send.return_value = requests.Response()
        real_send.return_value.status_code = 200
        requests.get(url)

        self.assertEqual(1, real_send.call_count)
        self.assertEqual(url, real_send.call_args[0][0].url)

    @requests_mock.Mocker()
    def test_with_test_decorator(self, m):
        self._do_test(m)

    @requests_mock.Mocker(kw='mock')
    def test_with_mocker_kwargs(self, **kwargs):
        self._do_test(kwargs['mock'])

    def test_with_decorator(self):

        @requests_mock.Mocker()
        def inner(m):
            self.assertMockStarted()
            self._do_test(m)

        self.assertMockStopped()
        inner()
        self.assertMockStopped()
