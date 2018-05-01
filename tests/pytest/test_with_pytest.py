import requests


def test_simple(requests_mock):
    requests_mock.get('https://httpbin.org/get', text='data')
    assert 'data' == requests.get('https://httpbin.org/get').text


class TestClass(object):

    def configure(self, requests_mock):
        requests_mock.get('https://httpbin.org/get', text='data')

    def test_one(self, requests_mock):
        self.configure(requests_mock)
        assert 'data' == requests.get('https://httpbin.org/get').text
