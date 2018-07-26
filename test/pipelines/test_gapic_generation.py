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

from artman import tasks
from artman.pipelines import code_generation
from artman.pipelines import gapic_generation
from artman.pipelines import grpc_generation


class GapicConfigPipelineTests(unittest.TestCase):
    @mock.patch.object(gapic_generation, 'GapicConfigTaskFactory')
    @mock.patch.object(code_generation.CodeGenerationPipelineBase, '__init__')
    def test_constructor(self, cgpb, gctf):
        gcp = gapic_generation.GapicConfigPipeline(foo='bar')
        cgpb.assert_called_once_with(gctf(), foo='bar')


class GapicClientPipelineTests(unittest.TestCase):
    @mock.patch.object(gapic_generation, 'GapicTaskFactory')
    @mock.patch.object(code_generation.CodeGenerationPipelineBase, '__init__')
    def test_constructor(self, cgpb, gctf):
        gcp = gapic_generation.GapicClientPipeline('csharp', foo='bar')
        cgpb.assert_called_once_with(gctf(), language='csharp', foo='bar')


class GapicConfigTaskFactoryTests(unittest.TestCase):
    def setUp(self):
        self._gctf = gapic_generation.GapicConfigTaskFactory()

    def test_get_validate_kwargs(self):
        COMMON_REQUIRED = code_generation.COMMON_REQUIRED
        assert self._gctf.get_validate_kwargs() == COMMON_REQUIRED

    def test_get_invalid_kwargs(self):
        assert self._gctf.get_invalid_kwargs() == ['language']

    def test_get_tasks(self):
        expected = (
            tasks.protoc.ProtoDescGenTask,
            tasks.gapic.GapicConfigGenTask,
            tasks.gapic.GapicConfigMoveTask,
        )
        instantiated_tasks = self._gctf.get_tasks()
        for task, class_ in zip(instantiated_tasks, expected):
            assert isinstance(task, class_)


class DiscoGapicConfigTaskFactoryTests(unittest.TestCase):
    def setUp(self):
        self._gctf = gapic_generation.DiscoGapicConfigTaskFactory()

    def test_get_validate_kwargs(self):
        COMMON_DISCO_REQUIRED = code_generation.COMMON_DISCO_REQUIRED
        assert self._gctf.get_validate_kwargs() == COMMON_DISCO_REQUIRED

    def test_get_invalid_kwargs(self):
        assert self._gctf.get_invalid_kwargs() == ['language']

    def test_get_tasks(self):
        expected = (
            tasks.gapic.DiscoGapicConfigGenTask,
            tasks.gapic.GapicConfigMoveTask,
        )
        instantiated_tasks = self._gctf.get_tasks()
        for task, class_ in zip(instantiated_tasks, expected):
            assert isinstance(task, class_)
