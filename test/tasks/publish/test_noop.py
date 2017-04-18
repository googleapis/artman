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
import os
import unittest

import mock

from artman.tasks.publish import noop
from artman.utils.logger import logger


class EmitSuccessTests(unittest.TestCase):
    def test_execute(self):
        task = noop.EmitSuccess()
        with mock.patch.object(logger, 'success') as success:
            task.execute(os.path.expanduser('~/foo/bar'))
            success.assert_called_once()
            _, args, _ = success.mock_calls[0]
            assert args[0].startswith('Code generated: ')
            assert args[0].endswith('~/foo/bar')
