try:
    from http import HTTPStatus
    HTTP_STATUS_FOUND = HTTPStatus.FOUND
except ImportError:
    from httplib import FOUND as HTTP_STATUS_FOUND

import pytest
import requests
import requests_mock


def test_simple(requests_mock):
    requests_mock.get('https://httpbin.org/get', text='data')
    assert 'data' == requests.get('https://httpbin.org/get').text


def test_redirect_and_nesting():
    url_inner = "inner-mock://example.test/"
    url_middle = "middle-mock://example.test/"
    url_outer = "outer-mock://example.test/"
    url_base = "https://www.example.com/"

    text_middle = 'middle' + url_middle
    text_outer = 'outer' + url_outer
    text_base = 'outer' + url_base

    with requests_mock.Mocker() as outer_mock:
        outer_mock.get(url_base, text=text_base)
        outer_mock.get(url_outer, text=text_outer)

        with requests_mock.Mocker(real_http=True) as middle_mock:
            middle_mock.get(url_middle, text=text_middle)

            with requests_mock.Mocker() as inner_mock:
                inner_mock.post(url_inner,
                                status_code=HTTP_STATUS_FOUND,
                                headers={'location': url_base})
                inner_mock.get(url_base, real_http=True)

                assert text_base == requests.post(url_inner).text  # nosec

                with pytest.raises(requests_mock.NoMockAddress):
                    requests.get(url_middle)

                with pytest.raises(requests_mock.NoMockAddress):
                    requests.get(url_outer)

            # back to middle mock
            with pytest.raises(requests_mock.NoMockAddress):
                requests.post(url_inner)

            assert text_middle == requests.get(url_middle).text  # nosec
            assert text_outer == requests.get(url_outer).text  # nosec

        # back to outter mock
        with pytest.raises(requests_mock.NoMockAddress):
            requests.post(url_inner)

        with pytest.raises(requests_mock.NoMockAddress):
            requests.get(url_middle)

        assert text_outer == requests.get(url_outer).text  # nosec


def test_mixed_mocks():
    url = 'mock://example.test/'
    with requests_mock.Mocker() as global_mock:
        global_mock.get(url, text='global')
        session = requests.Session()
        text = session.get(url).text
        assert text == 'global'  # nosec
        with requests_mock.Mocker(session=session) as session_mock:
            session_mock.get(url, real_http=True)
            text = session.get(url).text
            assert text == 'global'  # nosec


class TestClass(object):

    def configure(self, requests_mock):
        requests_mock.get('https://httpbin.org/get', text='data')

    def test_one(self, requests_mock):
        self.configure(requests_mock)
        assert 'data' == requests.get('https://httpbin.org/get').text
