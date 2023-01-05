import requests
import requests_mock

from . import base


class SessionCookiesTest(base.TestCase):
    def test_cookie(self):
        with requests_mock.Mocker() as mocker:
            cookies = {"name": "value", "name2": "value2"}
            mocker.get("mock://test.site", text="hello", cookies=cookies)

            with requests.Session() as session:
                resp = session.get("mock://test.site")

                self.assertEquals(resp.cookies.get("name"), "value")
                self.assertEquals(session.cookies.get("name"), "value")

                self.assertEquals(session.cookies.get("name2"), "value2")
