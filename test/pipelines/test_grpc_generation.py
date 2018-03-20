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
from artman.pipelines import batch_generation
from artman.pipelines import grpc_generation


class GrpcClientPipelineTests(unittest.TestCase):
    @mock.patch.object(grpc_generation, 'get_grpc_task_factory')
    @mock.patch.object(code_generation.CodeGenerationPipelineBase, '__init__')
    def test_constructor(self, cgpb, ggtf):
        grpc_generation.GrpcClientPipeline(foo='bar')
        cgpb.assert_called_once_with(ggtf(), foo='bar')


class ProtoClientPipelineTests(unittest.TestCase):
    @mock.patch.object(grpc_generation, 'get_proto_task_factory')
    @mock.patch.object(code_generation.CodeGenerationPipelineBase, '__init__')
    def test_constructor(self, cgpb, gptf):
        grpc_generation.ProtoClientPipeline(foo='bar')
        cgpb.assert_called_once_with(gptf(), foo='bar')


class GrpcTaskFactoryBaseTests(unittest.TestCase):
    def setUp(self):
        self._gtfb = grpc_generation.GrpcTaskFactoryBase()

    def test_get_validate_kwargs(self):
        COMMON_REQUIRED = code_generation.COMMON_REQUIRED
        assert self._gtfb.get_validate_kwargs() == COMMON_REQUIRED

    def test_get_invalid_kwargs(self):
        assert self._gtfb.get_invalid_kwargs() == []

    def test_get_tasks(self):
        expected = [protoc_tasks.GrpcPackmanTask]
        actual = self._gtfb.get_tasks(publish='noop')
        for task, class_ in zip(actual, expected):
            assert isinstance(task, class_)


class GrpcClientBatchPipelineTests(unittest.TestCase):
    @mock.patch.object(grpc_generation, '_make_grpc_batch_pipeline_tasks')
    @mock.patch.object(batch_generation.BatchPipeline, '__init__')
    def test_constructor(self, bp, mgbpt):
        grpc_generation.GrpcClientBatchPipeline(foo='bar')
        bp.assert_called_once_with(mgbpt, foo='bar')


class ProtoClientBatchPipelineTests(unittest.TestCase):
    @mock.patch.object(grpc_generation, '_make_proto_batch_pipeline_tasks')
    @mock.patch.object(batch_generation.BatchPipeline, '__init__')
    def test_constructor(self, bp, mpbpt):
        grpc_generation.ProtoClientBatchPipeline(foo='bar')
        bp.assert_called_once_with(mpbpt, foo='bar')


class MakeGrpcBatchPipelineTasksTest(unittest.TestCase):
    def test_make_java(self):
        expected = [
            protoc_tasks.ProtoDescGenTask,
            protoc_tasks.ProtoCodeGenTask,
            protoc_tasks.GrpcCodeGenTask,
            package_metadata_tasks.PackageMetadataConfigGenTask,
            package_metadata_tasks.ProtoPackageMetadataGenTask,
            package_metadata_tasks.GrpcPackageMetadataGenTask
        ]
        actual = grpc_generation._make_grpc_batch_pipeline_tasks(language='java')
        for task, class_ in zip(actual, expected):
            assert isinstance(task, class_)

    def test_no_language(self):
        with pytest.raises(ValueError):
            grpc_generation._make_grpc_batch_pipeline_tasks()

    def test_bad_language(self):
        with pytest.raises(ValueError):
            grpc_generation._make_grpc_batch_pipeline_tasks(language='cpp')


class MakeProtoBatchPipelineTasksTest(unittest.TestCase):
    def test_make_java(self):
        expected = [
            protoc_tasks.ProtoDescGenTask,
            protoc_tasks.ProtoCodeGenTask,
            package_metadata_tasks.PackageMetadataConfigGenTask,
            package_metadata_tasks.ProtoPackageMetadataGenTask,
            protoc_tasks.JavaProtoCopyTask,
        ]
        actual = grpc_generation._make_proto_batch_pipeline_tasks(language='java')
        for task, class_ in zip(actual, expected):
            assert isinstance(task, class_)

    def test_no_language(self):
        with pytest.raises(ValueError):
            grpc_generation._make_proto_batch_pipeline_tasks()

    def test_bad_language(self):
        with pytest.raises(ValueError):
            grpc_generation._make_proto_batch_pipeline_tasks(language='python')
