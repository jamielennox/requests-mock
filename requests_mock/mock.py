# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures
import requests

from requests_mock import adapter


class Mock(fixtures.Fixture):

    def __init__(self):
        super(Mock, self).__init__()
        self.adapter = adapter.Adapter()
        self._original_get_adapter = None

    def _cleanup(self):
        if not self._original_get_adapter:
            return

        requests.Session.get_adapter = self._original_get_adapter
        self._original_get_adapter = None

    def _get_adapter(self, url):
        return self.adapter

    def setUp(self):
        super(Mock, self).setUp()

        self._original_get_adapter = requests.Session.get_adapter
        requests.Session.get_adapter = self._get_adapter

        self.addCleanup(self._cleanup)

    def register_uri(self, *args, **kwargs):
        return self.adapter.register_uri(*args, **kwargs)

    def latest_request(self):
        return self.adapter.latest_request()
