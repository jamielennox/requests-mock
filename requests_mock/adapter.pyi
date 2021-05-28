# Stubs for requests_mock.adapter

from requests.adapters import BaseAdapter
from requests_mock import _RequestObjectProxy
from typing import Any, Callable, Dict, List, NewType, Optional, Pattern, Union

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
    def __call__(self, request: Any) -> Any: ...

class Adapter(BaseAdapter, _RequestHistoryTracker):
    def __init__(self, case_sensitive: bool = ...) -> None: ...
    def register_uri(
        self,
        method: Union[str, AnyMatcher],
        url: Union[str, Pattern[str], AnyMatcher],
        response_list: Optional[List[Dict[str, Any]]] = ...,
        request_headers: Dict[str, str] = ...,
        complete_qs: bool = ...,
        status_code: int = ...,
        text: str = ...,
        headers: Optional[Dict[str, str]] = ...,
        additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
        **kwargs: Any
    ) -> Any: ...
    def add_matcher(self, matcher: Any) -> None: ...
