try:
    from http import HTTPStatus
    HTTPStatus_FOUND = HTTPStatus.FOUND
except ImportError:
    from httplib import FOUND as HTTPStatus_FOUND

import requests


def test_simple(requests_mock):
    requests_mock.get('https://httpbin.org/get', text='data')
    assert 'data' == requests.get('https://httpbin.org/get').text


def test_redirect(requests_mock):
    url1 = "https://mocked.example.com/"
    url2 = "https://www.example.com/"
    requests_mock.post(url1, status_code=HTTPStatus_FOUND, headers={'location': url2})
    requests_mock.get(url2, real_http=True)

    requests.post(url1)


class TestClass(object):

    def configure(self, requests_mock):
        requests_mock.get('https://httpbin.org/get', text='data')

    def test_one(self, requests_mock):
        self.configure(requests_mock)
        assert 'data' == requests.get('https://httpbin.org/get').text
