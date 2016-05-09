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

import json
import re

import requests
import six
from six.moves.urllib import parse as urlparse

import requests_mock
from requests_mock.tests import base


class MyExc(Exception):
    pass


class SessionAdapterTests(base.TestCase):

    PREFIX = "mock"

    def setUp(self):
        super(SessionAdapterTests, self).setUp()

        self.adapter = requests_mock.Adapter()
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

        url_parts = urlparse.urlparse(self.url)
        qs = urlparse.parse_qs(url_parts.query)
        self.assertEqual(url_parts.scheme, self.adapter.last_request.scheme)
        self.assertEqual(url_parts.netloc, self.adapter.last_request.netloc)
        self.assertEqual(url_parts.path, self.adapter.last_request.path)
        self.assertEqual(url_parts.query, self.adapter.last_request.query)
        self.assertEqual(url_parts.query, self.adapter.last_request.query)
        self.assertEqual(qs, self.adapter.last_request.qs)

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
        self.adapter.register_uri(requests_mock.ANY, self.url, text='resp')

        for m in ('GET', 'HEAD', 'POST', 'UNKNOWN'):
            resp = self.session.request(m, self.url)
            self.assertEqual('resp', resp.text)

    def test_with_any_url(self):
        self.adapter.register_uri('GET', requests_mock.ANY, text='resp')

        for u in ('mock://a', 'mock://b', 'mock://c'):
            resp = self.session.get(u)
            self.assertEqual('resp', resp.text)

    def test_with_regexp(self):
        self.adapter.register_uri('GET', re.compile('tester.com'), text='resp')

        for u in ('mock://www.tester.com/a', 'mock://abc.tester.com'):
            resp = self.session.get(u)
            self.assertEqual('resp', resp.text)

    def test_requests_in_history_on_no_match(self):
        self.assertRaises(requests_mock.NoMockAddress,
                          self.session.get,
                          self.url)

        self.assertEqual(self.url, self.adapter.last_request.url)

    def test_requests_in_history_on_exception(self):

        def _test_cb(request, ctx):
            raise MyExc()

        self.adapter.register_uri('GET', self.url, text=_test_cb)

        self.assertRaises(MyExc,
                          self.session.get,
                          self.url)

        self.assertEqual(self.url, self.adapter.last_request.url)

    def test_not_called_and_called_count(self):
        m = self.adapter.register_uri('GET', self.url, text='resp')
        self.assertEqual(0, m.call_count)
        self.assertFalse(m.called)

        self.assertEqual(0, self.adapter.call_count)
        self.assertFalse(self.adapter.called)

    def test_called_and_called_count(self):
        m = self.adapter.register_uri('GET', self.url, text='resp')

        resps = [self.session.get(self.url) for i in range(0, 3)]

        for r in resps:
            self.assertEqual('resp', r.text)
            self.assertEqual(200, r.status_code)

        self.assertEqual(len(resps), m.call_count)
        self.assertTrue(m.called)

        self.assertEqual(len(resps), self.adapter.call_count)
        self.assertTrue(self.adapter.called)

    def test_adapter_picks_correct_adatper(self):
        good = '%s://test3.url/' % self.PREFIX
        self.adapter.register_uri('GET',
                                  '%s://test1.url' % self.PREFIX,
                                  text='bad')
        self.adapter.register_uri('GET',
                                  '%s://test2.url' % self.PREFIX,
                                  text='bad')
        self.adapter.register_uri('GET', good, text='good')
        self.adapter.register_uri('GET',
                                  '%s://test4.url' % self.PREFIX,
                                  text='bad')

        resp = self.session.get(good)

        self.assertEqual('good', resp.text)

    def test_adapter_is_connection(self):
        url = '%s://test.url' % self.PREFIX
        text = 'text'
        self.adapter.register_uri('GET', url, text=text)
        resp = self.session.get(url)

        self.assertEqual(text, resp.text)
        self.assertIs(self.adapter, resp.connection)

    def test_send_to_connection(self):
        url1 = '%s://test1.url/' % self.PREFIX
        url2 = '%s://test2.url/' % self.PREFIX

        text1 = 'text1'
        text2 = 'text2'

        self.adapter.register_uri('GET', url1, text=text1)
        self.adapter.register_uri('GET', url2, text=text2)

        req = requests.Request(method='GET', url=url2).prepare()

        resp1 = self.session.get(url1)
        self.assertEqual(text1, resp1.text)

        resp2 = resp1.connection.send(req)
        self.assertEqual(text2, resp2.text)

    def test_request_json_with_str_data(self):
        dict_req = {'hello': 'world'}
        dict_resp = {'goodbye': 'world'}

        m = self.adapter.register_uri('POST', self.url, json=dict_resp)

        data = json.dumps(dict_req)
        resp = self.session.post(self.url, data=data)

        self.assertIs(data, m.last_request.body)
        self.assertEqual(dict_resp, resp.json())
        self.assertEqual(dict_req, m.last_request.json())

    def test_request_json_with_bytes_data(self):
        dict_req = {'hello': 'world'}
        dict_resp = {'goodbye': 'world'}

        m = self.adapter.register_uri('POST', self.url, json=dict_resp)

        data = json.dumps(dict_req).encode('utf-8')
        resp = self.session.post(self.url, data=data)

        self.assertIs(data, m.last_request.body)
        self.assertEqual(dict_resp, resp.json())
        self.assertEqual(dict_req, m.last_request.json())

    def test_request_json_with_cb(self):
        dict_req = {'hello': 'world'}
        dict_resp = {'goodbye': 'world'}
        data = json.dumps(dict_req)

        def _cb(req, context):
            self.assertEqual(dict_req, req.json())
            return dict_resp

        m = self.adapter.register_uri('POST', self.url, json=_cb)
        resp = self.session.post(self.url, data=data)

        self.assertEqual(1, m.call_count)
        self.assertEqual(dict_resp, resp.json())

    def test_raises_exception(self):
        self.adapter.register_uri('GET', self.url, exc=MyExc)

        self.assertRaises(MyExc,
                          self.session.get,
                          self.url)

        self.assertEqual(self.url, self.adapter.last_request.url)

    def test_raises_exception_with_body_args_fails(self):
        self.assertRaises(TypeError,
                          self.adapter.register_uri,
                          'GET',
                          self.url,
                          exc=MyExc,
                          text='fail')

    def test_sets_request_matcher_in_history(self):
        url1 = '%s://test1.url/' % self.PREFIX
        url2 = '%s://test2.url/' % self.PREFIX

        text1 = 'text1'
        text2 = 'text2'

        m1 = self.adapter.register_uri('GET', url1, text=text1)
        m2 = self.adapter.register_uri('GET', url2, text=text2)

        resp1 = self.session.get(url1)
        resp2 = self.session.get(url2)

        self.assertEqual(text1, resp1.text)
        self.assertEqual(text2, resp2.text)

        self.assertEqual(2, self.adapter.call_count)

        self.assertEqual(url1, self.adapter.request_history[0].url)
        self.assertEqual(url2, self.adapter.request_history[1].url)

        self.assertIs(m1, self.adapter.request_history[0].matcher)
        self.assertIs(m2, self.adapter.request_history[1].matcher)

    def test_sets_request_matcher_on_exception(self):
        m = self.adapter.register_uri('GET', self.url, exc=MyExc)

        self.assertRaises(MyExc,
                          self.session.get,
                          self.url)

        self.assertEqual(self.url, self.adapter.last_request.url)
        self.assertIs(m, self.adapter.last_request.matcher)

    def test_cookies_from_header(self):
        headers = {'Set-Cookie': 'fig=newton; Path=/test; domain=.example.com'}
        self.adapter.register_uri('GET',
                                  self.url,
                                  text='text',
                                  headers=headers)

        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual(['/test'], resp.cookies.list_paths())
        self.assertEqual(['.example.com'], resp.cookies.list_domains())

    def test_cookies_from_dict(self):
        # This is a syntax we get from requests. I'm not sure i like it.
        self.adapter.register_uri('GET',
                                  self.url,
                                  text='text',
                                  cookies={'fig': 'newton', 'sugar': 'apple'})

        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual('apple', resp.cookies['sugar'])

    def test_cookies_with_jar(self):
        jar = requests_mock.CookieJar()
        jar.set('fig', 'newton', path='/foo', domain='.example.com')
        jar.set('sugar', 'apple', path='/bar', domain='.example.com')

        self.adapter.register_uri('GET', self.url, text='text', cookies=jar)
        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual('apple', resp.cookies['sugar'])
        self.assertEqual(set(['/foo', '/bar']), set(resp.cookies.list_paths()))
        self.assertEqual(['.example.com'], resp.cookies.list_domains())

    def test_cookies_header_with_cb(self):

        def _cb(request, context):
            val = 'fig=newton; Path=/test; domain=.example.com'
            context.headers['Set-Cookie'] = val
            return 'text'

        self.adapter.register_uri('GET', self.url, text=_cb)
        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual(['/test'], resp.cookies.list_paths())
        self.assertEqual(['.example.com'], resp.cookies.list_domains())

    def test_cookies_from_dict_with_cb(self):
        def _cb(request, context):
            # converted into a jar by now
            context.cookies.set('sugar', 'apple', path='/test')
            return 'text'

        self.adapter.register_uri('GET',
                                  self.url,
                                  text=_cb,
                                  cookies={'fig': 'newton'})

        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual('apple', resp.cookies['sugar'])
        self.assertEqual(['/', '/test'], resp.cookies.list_paths())

    def test_cookies_with_jar_cb(self):
        def _cb(request, context):
            context.cookies.set('sugar',
                                'apple',
                                path='/bar',
                                domain='.example.com')
            return 'text'

        jar = requests_mock.CookieJar()
        jar.set('fig', 'newton', path='/foo', domain='.example.com')

        self.adapter.register_uri('GET', self.url, text=_cb, cookies=jar)
        resp = self.session.get(self.url)

        self.assertEqual('newton', resp.cookies['fig'])
        self.assertEqual('apple', resp.cookies['sugar'])
        self.assertEqual(set(['/foo', '/bar']), set(resp.cookies.list_paths()))
        self.assertEqual(['.example.com'], resp.cookies.list_domains())

    def test_base_params(self):
        data = 'testdata'
        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url)

        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)

        self.assertIs(None, self.adapter.last_request.allow_redirects)
        self.assertIs(None, self.adapter.last_request.timeout)
        self.assertIs(True, self.adapter.last_request.verify)
        self.assertIs(None, self.adapter.last_request.cert)

        # actually it's an OrderedDict, but equality works fine
        self.assertEqual({}, self.adapter.last_request.proxies)

    def test_allow_redirects(self):
        data = 'testdata'
        self.adapter.register_uri('GET', self.url, text=data, status_code=300)
        resp = self.session.get(self.url, allow_redirects=False)

        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(300, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertFalse(self.adapter.last_request.allow_redirects)

    def test_timeout(self):
        data = 'testdata'
        timeout = 300

        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url, timeout=timeout)

        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertEqual(timeout, self.adapter.last_request.timeout)

    def test_verify_false(self):
        data = 'testdata'
        verify = False

        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url, verify=verify)
        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertIs(verify, self.adapter.last_request.verify)

    def test_verify_path(self):
        data = 'testdata'
        verify = '/path/to/cacerts.pem'

        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url, verify=verify)
        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertEqual(verify, self.adapter.last_request.verify)

    def test_certs(self):
        data = 'testdata'
        cert = ('/path/to/cert.pem', 'path/to/key.pem')

        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url, cert=cert)

        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertEqual(cert, self.adapter.last_request.cert)
        self.assertTrue(self.adapter.last_request.verify)

    def test_proxies(self):
        data = 'testdata'
        proxies = {'http': 'foo.bar:3128',
                   'http://host.name': 'foo.bar:4012'}

        self.adapter.register_uri('GET', self.url, text=data)
        resp = self.session.get(self.url, proxies=proxies)

        self.assertEqual('GET', self.adapter.last_request.method)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(data, resp.text)
        self.assertEqual(proxies, self.adapter.last_request.proxies)
        self.assertIsNot(proxies, self.adapter.last_request.proxies)
