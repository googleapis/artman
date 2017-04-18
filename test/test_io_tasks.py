# Copyright 2016 Google Inc. All Rights Reserved.
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

import unittest

from artman.tasks import io_tasks


_UPLOAD_LIMIT = 123


class ValidateUploadSizeTest(unittest.TestCase):

    def test_validate_upload_size_ok(self):
        io_tasks._validate_upload_size(_UPLOAD_LIMIT, _UPLOAD_LIMIT)

    def test_validate_upload_size_bad(self):
        self.assertRaises(
            ValueError, io_tasks._validate_upload_size,
            _UPLOAD_LIMIT + 1, _UPLOAD_LIMIT)
