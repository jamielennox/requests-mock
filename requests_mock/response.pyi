# Stubs for requests_mock.response

import six
from requests.cookies import RequestsCookieJar
from typing import Any

class CookieJar(RequestsCookieJar):
    def set(self, name: Any, value: Any, **kwargs: Any) -> Any: ...

class _FakeConnection:
    def send(self, request: Any, **kwargs: Any) -> None: ...
    def close(self) -> None: ...

class _IOReader(six.BytesIO):
    def read(self, *args: Any, **kwargs: Any) -> Any: ...

def create_response(request: Any, **kwargs: Any) -> Any: ...

class _Context:
    headers: Any = ...
    status_code: Any = ...
    reason: Any = ...
    cookies: Any = ...
    def __init__(self, headers: Any, status_code: Any, reason: Any, cookies: Any) -> None: ...

class _MatcherResponse:
    def __init__(self, **kwargs: Any) -> None: ...
    def get_response(self, request: Any) -> Any: ...