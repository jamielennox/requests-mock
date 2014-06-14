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

from requests_mock import adapter
from requests_mock.tests import base


class TestMatcher(base.TestCase):

    def match(self, target, url, complete_qs=False):
        matcher = adapter._Matcher('GET', target, [], complete_qs)
        request = requests.Request('GET', url).prepare()
        return matcher.match(request)

    def assertMatch(self, target, url, **kwargs):
        self.assertEqual(True, self.match(target, url, **kwargs),
                         'Matcher %s failed to match %s' % (target, url))

    def assertMatchBoth(self, target, url, **kwargs):
        self.assertMatch(target, url, **kwargs)
        self.assertMatch(url, target, **kwargs)

    def assertNoMatch(self, target, url, **kwargs):
        self.assertEqual(False, self.match(target, url, **kwargs),
                         'Matcher %s unexpectedly matched %s' % (target, url))

    def assertNoMatchBoth(self, target, url, **kwargs):
        self.assertNoMatch(target, url, **kwargs)
        self.assertNoMatch(url, target, **kwargs)

    def test_url_matching(self):
        self.assertMatchBoth('http://www.test.com',
                             'http://www.test.com')
        self.assertMatchBoth('http://www.test.com',
                             'http://www.test.com/')
        self.assertMatchBoth('http://www.test.com/abc',
                             'http://www.test.com/abc')
        self.assertMatchBoth('http://www.test.com:5000/abc',
                             'http://www.test.com:5000/abc')

        self.assertNoMatchBoth('https://www.test.com',
                               'http://www.test.com')
        self.assertNoMatchBoth('http://www.test.com/abc',
                               'http://www.test.com')
        self.assertNoMatchBoth('http://test.com',
                               'http://www.test.com')
        self.assertNoMatchBoth('http://test.com',
                               'http://www.test.com')
        self.assertNoMatchBoth('http://test.com/abc',
                               'http://www.test.com/abc/')
        self.assertNoMatchBoth('http://test.com/abc/',
                               'http://www.test.com/abc')
        self.assertNoMatchBoth('http://test.com:5000/abc/',
                               'http://www.test.com/abc')
        self.assertNoMatchBoth('http://test.com/abc/',
                               'http://www.test.com:5000/abc')

    def test_subset_match(self):
        self.assertMatch('/path', 'http://www.test.com/path')
        self.assertMatch('/path', 'http://www.test.com/path')
        self.assertMatch('//www.test.com/path', 'http://www.test.com/path')
        self.assertMatch('//www.test.com/path', 'https://www.test.com/path')

    def test_query_string(self):
        self.assertMatch('/path?a=1&b=2',
                         'http://www.test.com/path?a=1&b=2')
        self.assertMatch('/path?a=1',
                         'http://www.test.com/path?a=1&b=2',
                         complete_qs=False)
        self.assertNoMatch('/path?a=1',
                           'http://www.test.com/path?a=1&b=2',
                           complete_qs=True)
        self.assertNoMatch('/path?a=1&b=2',
                           'http://www.test.com/path?a=1')
