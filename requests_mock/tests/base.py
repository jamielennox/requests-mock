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

import os
import tempfile

import six
import testtools


class TestCase(testtools.TestCase):

    def create_tempfile(self, content, suffix='', prefix='tmp'):
        fd, filename = tempfile.mkstemp(suffix=suffix,
                                        prefix=prefix,
                                        text=False)
        self.addCleanup(os.unlink, filename)

        if isinstance(content, six.string_types):
            content = content.encode('utf-8')

        try:
            os.write(fd, content)
        finally:
            os.close(fd)

        return filename
