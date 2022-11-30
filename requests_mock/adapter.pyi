# Stubs for requests_mock.adapter

from http.cookiejar import CookieJar
from io import IOBase
from typing import Any, Callable, Dict, List, NewType, Optional, Pattern, Type, Union

from requests import Request, Response
from requests.adapters import BaseAdapter
from requests.packages.urllib3.response import HTTPResponse

from requests_mock.request import _RequestObjectProxy
from requests_mock.response import _Context

AnyMatcher = NewType("AnyMatcher", object)

ANY: AnyMatcher = ...

class _RequestHistoryTracker:
    request_history: List[_RequestObjectProxy] = ...
    def __init__(self) -> None: ...
    @property
    def last_request(self) -> Optional[_RequestObjectProxy]: ...
    @property
    def called(self) -> bool: ...
    @property
    def called_once(self) -> bool: ...
    @property
    def call_count(self) -> int: ...

class _RunRealHTTP(Exception): ...

class _Matcher(_RequestHistoryTracker):
    def __init__(self, method: Any, url: Any, responses: Any, complete_qs: Any, request_headers: Any, additional_matcher: Any, real_http: Any, case_sensitive: Any) -> None: ...
    def __call__(self, request: Request) -> Optional[Response]: ...

class Adapter(BaseAdapter, _RequestHistoryTracker):
    def __init__(self, case_sensitive: bool = ...) -> None: ...
    def register_uri(
        self,
        method: Union[str, AnyMatcher],
        url: Union[str, Pattern[str], AnyMatcher],
        response_list: Optional[List[Dict[str, Any]]] = ...,
        *,
        request_headers: Dict[str, str] = ...,
        complete_qs: bool = ...,
        status_code: int = ...,
        reason: str = ...,
        headers: Dict[str, str] = ...,
        cookies: Union[CookieJar, Dict[str, str]] = ...,
        json: Union[Any, Callable[[_RequestObjectProxy, _Context], Any]] = ...,
        text: Union[str, Callable[[_RequestObjectProxy, _Context], str]] = ...,
        content: Union[bytes, Callable[[_RequestObjectProxy, _Context], bytes]] = ...,
        body: Union[IOBase, Callable[[_RequestObjectProxy, _Context], IOBase]] = ...,
        raw: HTTPResponse = ...,
        exc: Union[Exception, Type[Exception]] = ...,
        additional_matcher: Callable[[_RequestObjectProxy], bool] = ...,
        **kwargs: Any
    ) -> _Matcher: ...
    def add_matcher(self, matcher: Callable[[Request], Optional[Response]]) -> None: ...
    def reset(self) -> None: ...