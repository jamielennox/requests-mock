# Stubs for requests_mock.mocker

from requests import Response
from requests_mock.request import _RequestObjectProxy
from typing import Any, Callable, Dict, List, Optional, Pattern, Type, TypeVar, Union

DELETE: str
GET: str
HEAD: str
OPTIONS: str
PATCH: str
POST: str
PUT: str

class MockerCore:
    case_sensitive: bool = ...
    def __init__(self, **kwargs: Any) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def add_matcher(self, matcher: Any) -> None: ...
    @property
    def request_history(self) -> List[_RequestObjectProxy]: ...
    @property
    def last_request(self) -> Optional[_RequestObjectProxy]: ...
    @property
    def called(self) -> bool: ...
    @property
    def called_once(self) -> bool: ...
    @property
    def call_count(self) -> int: ...
    def register_uri(
      self,
      method: str,
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def request(
      self,
      method: str,
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def get(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def head(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def options(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def post(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def put(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def patch(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...
    def delete(
      self,
      path: Union[str, Pattern[str]],
      status_code: int = ...,
      text: str = ...,
      headers: Optional[Dict[str, str]] = ...,
      additional_matcher: Optional[Callable[[_RequestObjectProxy], bool]] = ...,
      **kwargs: Any) -> Response: ...

_T = TypeVar('_T')

class Mocker(MockerCore):
    TEST_PREFIX: str = ...
    def __init__(
      self,
      kw: str = ...,
      case_sensitive: bool = ...,
      adapter: Any = ...,
      real_http: bool = ...) -> None: ...
    def __enter__(self) -> Any: ...
    def __exit__(self, type: Any, value: Any, traceback: Any) -> None: ...
    def __call__(self, obj: Any) -> Any: ...
    def copy(self) -> Mocker: ...
    def decorate_callable(self, func: Callable[..., _T]) -> Callable[..., _T]: ...
    def decorate_class(self, klass: Type[_T]) -> Type[_T]: ...
mock = Mocker
