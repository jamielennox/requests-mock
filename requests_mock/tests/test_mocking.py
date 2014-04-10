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
import requests_mock
from requests_mock.tests import base


class MockingTests(base.TestCase):

    def setUp(self):
        super(MockingTests, self).setUp()
        self.mocker = self.useFixture(requests_mock.Mock())

    def test_basic_install(self):
        pass

    def test_failure(self):
        self.assertRaises(requests_mock.NoMockAddress,
                          requests.get, 'http://www.google.com')

    def test_mock(self):
        test_url = 'http://www.google.com/'
        self.mocker.register_uri('GET', test_url, body='response')

        resp = requests.get(test_url)
        self.assertEqual('response', resp.text)
        self.assertEqual(test_url, self.mocker.latest_request().url)
