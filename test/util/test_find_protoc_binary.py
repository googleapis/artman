# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import unittest
import os

from artman.utils import protoc_utils


class FindProtoBinaryTest(unittest.TestCase):
    TESTDATA = os.path.join(
        os.path.realpath(os.path.dirname(__file__)), 'testdata')

    # Assert that the existing Dockerfile has a protoc binary.
    def test_protoc_binary_name_live(self):
        python_protoc = protoc_utils.protoc_binary_name('python')
        self.assertTrue(python_protoc)

    def test_parse_protoc_binary_name(self):
        for language in ['java', 'nodejs', 'php', 'go', 'python', 'ruby', 'csharp']:
            self._test(language)

    def _test(self, language):
        protoc_binary = protoc_utils.protoc_binary_name(language)
        self.assertTrue(protoc_binary)


if __name__ == '__main__':
    unittest.main()