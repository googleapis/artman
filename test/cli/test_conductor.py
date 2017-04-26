# Copyright 2017 Google
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import unittest

import pytest

from artman.cli import conductor


class ParseArgsTests(unittest.TestCase):
    def test_no_args(self):
        with pytest.raises(SystemExit):
            conductor._parse_args()

    def test_args(self):
        flags = conductor._parse_args(
            '--queue-name',
            'projects/foo/locations/bar/queues/baz',
            '-l')
        assert flags.queue_name == 'projects/foo/locations/bar/queues/baz'
        assert flags.log_local is True
