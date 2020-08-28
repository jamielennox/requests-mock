import requests
import requests_mock

from . import base


class SessionCookiesTest(base.TestCase):
    def test_cookie(self):
        with requests_mock.Mocker() as m:
            m.get("mock://test.site", text="hello", cookies={"name": "value"})

            with requests.Session() as s:
                r = s.get("mock://test.site")

                self.assertEquals(r.cookies.get("name"), "value")
                self.assertEquals(s.cookies.get("name"), "value")