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

import uuid

import requests
import requests_mock
from requests_mock.tests import base


class RequestTests(base.TestCase):

    def setUp(self):
        super(RequestTests, self).setUp()

        self.mocker = requests_mock.Mocker()
        self.addCleanup(self.mocker.stop)
        self.mocker.start()

    def do_request(self, **kwargs):
        method = kwargs.pop('method', 'GET')
        url = kwargs.pop('url', 'http://test.example.com/path')
        status_code = kwargs.pop('status_code', 200)
        data = uuid.uuid4().hex

        m = self.mocker.register_uri(method,
                                     url,
                                     text=data,
                                     status_code=status_code)

        resp = requests.request(method, url, **kwargs)

        self.assertEqual(status_code, resp.status_code)
        self.assertEqual(data, resp.text)

        self.assertTrue(m.called_once)
        return m.last_request

    def test_base_params(self):
        req = self.do_request(method='GET', status_code=200)

        self.assertIs(None, req.allow_redirects)
        self.assertIs(None, req.timeout)
        self.assertIs(True, req.verify)
        self.assertIs(None, req.cert)

        # actually it's an OrderedDict, but equality works fine
        self.assertEqual({}, req.proxies)

    def test_allow_redirects(self):
        req = self.do_request(allow_redirects=False, status_code=300)
        self.assertFalse(req.allow_redirects)

    def test_timeout(self):
        timeout = 300
        req = self.do_request(timeout=timeout)
        self.assertEqual(timeout, req.timeout)

    def test_verify_false(self):
        verify = False
        req = self.do_request(verify=verify)
        self.assertIs(verify, req.verify)

    def test_verify_path(self):
        verify = '/path/to/cacerts.pem'
        req = self.do_request(verify=verify)
        self.assertEqual(verify, req.verify)

    def test_certs(self):
        cert = ('/path/to/cert.pem', 'path/to/key.pem')
        req = self.do_request(cert=cert)
        self.assertEqual(cert, req.cert)
        self.assertTrue(req.verify)

    def test_proxies(self):
        proxies = {'http': 'foo.bar:3128',
                   'http://host.name': 'foo.bar:4012'}

        req = self.do_request(proxies=proxies)

        self.assertEqual(proxies, req.proxies)
        self.assertIsNot(proxies, req.proxies)

    def test_hostname_port_http(self):
        req = self.do_request(url='http://host.example.com:81/path')

        self.assertEqual('host.example.com:81', req.netloc)
        self.assertEqual('host.example.com', req.hostname)
        self.assertEqual(81, req.port)

    def test_hostname_port_https(self):
        req = self.do_request(url='https://host.example.com:8080/path')

        self.assertEqual('host.example.com:8080', req.netloc)
        self.assertEqual('host.example.com', req.hostname)
        self.assertEqual(8080, req.port)

    def test_hostname_default_port_http(self):
        req = self.do_request(url='http://host.example.com/path')

        self.assertEqual('host.example.com', req.netloc)
        self.assertEqual('host.example.com', req.hostname)
        self.assertEqual(80, req.port)

    def test_hostname_default_port_https(self):
        req = self.do_request(url='https://host.example.com/path')

        self.assertEqual('host.example.com', req.netloc)
        self.assertEqual('host.example.com', req.hostname)
        self.assertEqual(443, req.port)

    def test_form_data(self):
        req = self.do_request(method='POST', data={'abc': 'def', 'ghi': 'jkl'})
        self.assertEqual({'abc': ['def'], 'ghi': ['jkl']}, req.form())

    def test_bad_form_data(self):
        req = self.do_request(method='POST', data='abcd')
        self.assertEqual('abcd', req.text)
        self.assertRaises(ValueError, req.form)

    def test_form_data_spaces(self):
        data = {'abc': 'def', 'ghi': 'jkl mno-pq'}
        req = self.do_request(method='POST', data=data)
        self.assertEqual({'abc': ['def'], 'ghi': ['jkl mno-pq']}, req.form())

    def assertMultipartEqual(self, multi, filename=None, data=None,
                             content_type=None, headers=None):
        self.assertEqual(filename, multi.filename)
        self.assertEqual(data, multi.data)

        self.assertEqual(data, multi)
        self.assertEqual((filename, data), multi)

        if content_type:
            self.assertEqual(content_type, multi.content_type)
            self.assertEqual((filename, data, content_type), multi)

        if headers:
            for k, v in headers.items():
                self.assertEqual(v, multi.headers[k])

    def test_multipart_from_single_file(self):
        filename = 'filename'
        data = 'some test data'
        content_type = 'text/plain'
        file1 = self.create_tempfile(data)

        with open(file1, 'rb') as fd1:
            files = {'testfile': (filename, fd1, content_type)}
            req = self.do_request(method='POST', files=files)

        multi = req.multipart_form()

        self.assertEqual(set(['testfile']), set(multi.keys()))
        self.assertEqual(1, len(multi['testfile']))

        self.assertMultipartEqual(multi['testfile'][0],
                                  filename=filename,
                                  data=data.encode('utf-8'),
                                  content_type=content_type)

    def test_multipart_from_seperate_file_and_text(self):
        filename1 = 'filename'
        data1 = 'some test data'
        content_type1 = 'text/plain'

        filename2 = 'dataname'
        data2 = 'some different data'
        content_type2 = 'image/png'

        file1 = self.create_tempfile(data1)

        with open(file1, 'rb') as fd1:
            files = {'testfile': (filename1, fd1, content_type1),
                     'testdata': (filename2, data2, content_type2)}
            req = self.do_request(method='POST', files=files)

        multi = req.multipart_form()

        self.assertEqual(set(['testfile', 'testdata']), set(multi.keys()))
        self.assertEqual(1, len(multi['testfile']))
        self.assertEqual(1, len(multi['testdata']))

        self.assertMultipartEqual(multi['testfile'][0],
                                  filename=filename1,
                                  data=data1.encode('utf-8'),
                                  content_type=content_type1)

        self.assertMultipartEqual(multi['testdata'][0],
                                  filename=filename2,
                                  data=data2.encode('utf-8'),
                                  content_type=content_type2)

    def test_multipart_from_multi_file_and_text(self):
        filename1 = 'filename'
        data1 = 'some test data'
        content_type1 = 'text/plain'

        filename2 = 'dataname'
        data2 = 'some different data'
        content_type2 = 'image/png'

        file1 = self.create_tempfile(data1)

        with open(file1, 'rb') as fd1:
            files = [('testfile', (filename1, fd1, content_type1)),
                     ('testfile', (filename2, data2, content_type2))]

            req = self.do_request(method='POST', files=files)

        multi = req.multipart_form()

        self.assertEqual(set(['testfile']), set(multi.keys()))
        self.assertEqual(2, len(multi['testfile']))

        self.assertMultipartEqual(multi['testfile'][0],
                                  filename=filename1,
                                  data=data1.encode('utf-8'),
                                  content_type=content_type1)

        self.assertMultipartEqual(multi['testfile'][1],
                                  filename=filename2,
                                  data=data2.encode('utf-8'),
                                  content_type=content_type2)

    def test_multipart_from_multi_file_and_data(self):
        filename1 = 'filename'
        data1 = 'some test data'
        content_type1 = 'text/plain'

        filename2 = 'dataname'
        data2 = 'some different data'
        content_type2 = 'image/png'

        file1 = self.create_tempfile(data1)

        with open(file1, 'rb') as fd1:
            files = [('testfile', (filename1, fd1, content_type1)),
                     ('testfile', (filename2, data2, content_type2))]

            req = self.do_request(method='POST',
                                  files=files,
                                  data={'a': 'b', 'c': 'd'})

        multi = req.multipart_form()

        self.assertEqual(set(['testfile', 'a', 'c']), set(multi.keys()))

        self.assertEqual(2, len(multi['testfile']))
        self.assertEqual(1, len(multi['a']))
        self.assertEqual(1, len(multi['c']))

        self.assertMultipartEqual(multi['testfile'][0],
                                  filename=filename1,
                                  data=data1.encode('utf-8'),
                                  content_type=content_type1)

        self.assertMultipartEqual(multi['testfile'][1],
                                  filename=filename2,
                                  data=data2.encode('utf-8'),
                                  content_type=content_type2)

        self.assertMultipartEqual(multi['a'][0],
                                  filename=None,
                                  data='b')

        self.assertMultipartEqual(multi['c'][0],
                                  filename=None,
                                  data='d')
