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
import uuid

import mock

import pytest

from taskflow.patterns import linear_flow

from artman.pipelines import code_generation
from artman.pipelines import gapic_generation
from artman.pipelines import pipeline_base
from artman.tasks import io_tasks
from artman.utils import pipeline_util


class CodeGenerationPipelineBaseTests(unittest.TestCase):
    @mock.patch.object(pipeline_base.PipelineBase, '__init__')
    @mock.patch.object(uuid, 'uuid4')
    def test_constructor(self, uuid4, super_init):
        uuid4.return_value = '00000000'
        cgpb = code_generation.CodeGenerationPipelineBase(None,
            remote_mode=True,
        )

        # Assert that the superclass constructor was called.
        super_init.assert_called_once()

        # Assert that the expected keyword arguments were sent.
        _, _, kwargs = super_init.mock_calls[0]
        assert len(kwargs) == 5
        assert kwargs['tarfile'] == '00000000.tar.gz'
        assert kwargs['bucket_name'] == 'pipeline'
        assert kwargs['src_path'] == '00000000.tar.gz'
        assert kwargs['dest_path'].endswith('00000000.tar.gz')
        assert kwargs['remote_mode'] is True

    @mock.patch.object(pipeline_base.PipelineBase, '__init__')
    def test_constructor_not_remote_mode(self, super_init):
        cgpb = code_generation.CodeGenerationPipelineBase(None,
            remote_mode=False,
        )

        # Assert that the superclass constructor was called.
        super_init.assert_called_once()

        # Assert that the expected keyword arguments were sent.
        _, _, kwargs = super_init.mock_calls[0]
        assert len(kwargs) == 1
        assert kwargs['remote_mode'] is False

    def test_do_build_flow(self):
        CGPB = code_generation.CodeGenerationPipelineBase
        with mock.patch.object(CGPB, 'validate_kwargs') as validate:
            cgpb = CGPB(
                gapic_generation.GapicTaskFactory(),
                language='python', publish='noop'
            )
            validate.assert_called_once()
        flow = cgpb.do_build_flow(language='python', publish='noop',
                                  gapic_code_dir='output')
        assert isinstance(flow, linear_flow.Flow)
        assert len(flow) == 9

    def test_do_build_flow_disco(self):
        CGPB = code_generation.CodeGenerationPipelineBase
        with mock.patch.object(CGPB, 'validate_kwargs') as validate:
            cgpb = CGPB(
                gapic_generation.DiscoGapicTaskFactory(),
                language='java', publish='noop'
            )
            validate.assert_called_once()
        flow = cgpb.do_build_flow(language='java', publish='noop',
                                  gapic_code_dir='output')
        assert isinstance(flow, linear_flow.Flow)
        assert len(flow) == 6

    def test_do_build_flow_no_gapic(self):
        CGPB = code_generation.CodeGenerationPipelineBase
        with mock.patch.object(CGPB, 'validate_kwargs') as validate:
            cgpb = CGPB(
                gapic_generation.GapicTaskFactory(),
                language='python', publish='noop'
            )
            validate.assert_called_once()
        flow = cgpb.do_build_flow(language='python', publish='noop')
        assert isinstance(flow, linear_flow.Flow)
        assert len(flow) == 7

    @mock.patch.object(pipeline_util, 'validate_exists')
    @mock.patch.object(pipeline_util, 'validate_does_not_exist')
    def test_validation(self, does_not_exist, does_exist):
        gtf = gapic_generation.GapicTaskFactory()
        gcpb = code_generation.CodeGenerationPipelineBase(gtf,
            language='python',
            publish='noop',
        )
        does_exist.assert_called_once()
        does_not_exist.assert_called_once()

    def test_additional_remote_tasks(self):
        CGPB = code_generation.CodeGenerationPipelineBase
        with mock.patch.object(CGPB, 'validate_kwargs') as validate:
            cgpb = CGPB(
                gapic_generation.GapicTaskFactory(),
                language='python', publish='noop',
            )
            validate.assert_called_once()
        remote_tasks = cgpb.additional_tasks_for_remote_execution()
        assert len(remote_tasks) == 3

        # Check that we got the actual tasks that we expect.
        expected = (
            io_tasks.PrepareUploadDirTask,
            io_tasks.BlobUploadTask,
            io_tasks.CleanupTempDirsTask,
        )
        for task, class_ in zip(remote_tasks, expected):
            assert isinstance(task, class_)


class TaskFactoryBaseTests(unittest.TestCase):
    def test_get_tasks_nie(self):
        tfb = code_generation.TaskFactoryBase()
        with pytest.raises(NotImplementedError):
            assert tfb.get_tasks()

    def test_get_validate_kwargs_nie(self):
        tfb = code_generation.TaskFactoryBase()
        with pytest.raises(NotImplementedError):
            assert tfb.get_validate_kwargs()

    def test_get_invalid_kwargs_nie(self):
        tfb = code_generation.TaskFactoryBase()
        with pytest.raises(NotImplementedError):
            assert tfb.get_invalid_kwargs()
