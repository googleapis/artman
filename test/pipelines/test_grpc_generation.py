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

import mock

import pytest

from artman.tasks import protoc_tasks, package_metadata_tasks
from artman.pipelines import code_generation
from artman.pipelines import grpc_generation


class ProtoGenTaskFactoryTests(unittest.TestCase):
    def setUp(self):
        self._gtfb = grpc_generation.ProtoGenTaskFactory(gen_grpc=True,
                                                         language='java',
                                                         aspect='ALL')

    def test_get_validate_kwargs(self):
        COMMON_REQUIRED = code_generation.COMMON_REQUIRED
        assert self._gtfb.get_validate_kwargs() == COMMON_REQUIRED

    def test_get_invalid_kwargs(self):
        assert self._gtfb.get_invalid_kwargs() == []

    def test_get_tasks(self):
        expected = []
        actual = self._gtfb.get_tasks(publish='noop')
        for task, class_ in zip(actual, expected):
            assert isinstance(task, class_)
