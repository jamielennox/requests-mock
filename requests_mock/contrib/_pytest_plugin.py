import pytest
import requests_mock as rm_module


def pytest_addoption(parser):
    parser.addini('requests_mock_case_sensitive',
                  'Use case sensitive matching in requests_mock',
                  type='bool',
                  default=False)


@pytest.fixture(scope='function')  # executed on every test
def requests_mock(request):
    kw = {
        'case_sensitive': request.config.getini('requests_mock_case_sensitive')
    }

    with rm_module.Mocker(**kw) as m:
        yield m
