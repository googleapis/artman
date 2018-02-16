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

from taskflow.patterns import linear_flow

from artman import tasks
from artman.pipelines import batch_generation
from artman.pipelines import gapic_generation
from artman.pipelines import grpc_generation


def make_empty_task(**kwargs):
    return tasks.EmptyTask()


def make_tasks(**kwargs):
    tf = gapic_generation.GapicTaskFactory()
    return tf.get_tasks(**kwargs)


class BatchTaskFactoryTests(unittest.TestCase):
    def setUp(self):
        self._btf = batch_generation.BatchTaskFactory(make_empty_task)
        self._kwargs = {
            'batch_apis': '*',
            'exclude_apis': ['test/cli/data/gapic/api/artman_longrunning.yaml'],
            'language': 'python',
            'api_config_patterns': ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml'],
            'artman_language_yaml': 'test/cli/data/gapic/lang/common.yaml',
            'toolkit': '/toolkit',
            'root_dir': '/googleapis',
            'publish': 'noop',
        }

    def test_validate_kwargs(self):
        expected = ['batch_apis', 'language', 'api_config_patterns',
                    'artman_language_yaml', 'publish']
        assert self._btf.get_validate_kwargs() == expected

    def test_invalid_kwargs(self):
        assert self._btf.get_invalid_kwargs() == []

    def test_get_tasks(self):
        with mock.patch.object(self._btf, 'get_language_api_flows') as get:
            get.return_value = [make_empty_task()]
            tasks = self._btf.get_tasks()
            assert len(tasks) == 1
            assert isinstance(tasks[0], linear_flow.Flow)

    def test_get_language_api_flows_tasks(self):
        self._kwargs['batch_apis'] = ['pubsub']
        expected = [
            tasks.protoc.ProtoDescGenTask,
            tasks.package_metadata.PackageMetadataConfigGenTask,
            tasks.gapic.GapicCodeGenTask,
            tasks.format.PythonFormatTask,
        ]
        self._btf.make_pipeline_tasks_func = make_tasks
        flows = self._btf.get_language_api_flows(**self._kwargs)
        instantiated_tasks = []
        for flow in flows:
            for task, _ in flow.iter_nodes():
                instantiated_tasks.append(task)
        for task, class_ in zip(instantiated_tasks, expected):
            assert isinstance(task, class_)

    def test_get_language_api_flows_list(self):
        self._kwargs['batch_apis'] = ['pubsub', 'longrunning']
        self._kwargs['exclude_apis'] = []
        with mock.patch.object(self._btf, 'make_single_language_flow') as make:
            apis = []
            for x in self._btf.get_language_api_flows(**self._kwargs):
                assert x == make.return_value
                _, kw = make.call_args
                apis.append(kw['api_name'])
            assert make.call_count == 2
            assert apis == ['pubsub', 'longrunning']

    def test_get_language_api_flows_list_exclude(self):
        self._kwargs['batch_apis'] = ['longrunning']
        with pytest.raises(ValueError):
            with mock.patch.object(self._btf, 'make_single_language_flow'):
                list(self._btf.get_language_api_flows(**self._kwargs))

    def test_get_language_api_flows(self):
        with mock.patch.object(self._btf, 'make_single_language_flow') as make:
            apis = []
            for x in self._btf.get_language_api_flows(**self._kwargs):
                assert x == make.return_value
                _, kw = make.call_args
                print('kw:', kw)
                apis.append(kw['api_name'])
            assert make.call_count == 2
            assert apis == ['logging', 'pubsub']

    def test_get_language_api_flows_publish(self):
        staging_repo = {'location': 'staging_repo.git'}
        self._kwargs['publish'] = 'github'
        self._kwargs['git_repos'] = {
            'staging': staging_repo
        }
        with mock.patch.object(self._btf, 'make_single_language_flow') as make:
            for x in self._btf.get_language_api_flows(**self._kwargs):
                _, kw = make.call_args
                assert kw['git_repo'] == staging_repo


def test_get_artman_config_filenames_wildcard():
    api_config_patterns = ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml',
                           'test/cli/data/gapic/core/artman_${API_SHORT_NAME}.yaml']
    expected = [
        'test/cli/data/gapic/api/artman_logging.yaml',
        'test/cli/data/gapic/api/artman_longrunning.yaml',
        'test/cli/data/gapic/api/artman_pubsub.yaml',
        'test/cli/data/gapic/core/artman_core.yaml',
    ]
    actual = batch_generation._get_artman_config_filenames(
            api_config_patterns, '*', [])
    assert expected == actual


def test_get_artman_config_filenames_wildcard_exclude():
    api_config_patterns = ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml',
                           'test/cli/data/gapic/core/artman_${API_SHORT_NAME}.yaml']
    exclude_apis = [
        'test/cli/data/gapic/api/artman_longrunning.yaml',
        'test/cli/data/gapic/core/artman_core.yaml',
    ]
    expected = [
        'test/cli/data/gapic/api/artman_logging.yaml',
        'test/cli/data/gapic/api/artman_pubsub.yaml',
    ]
    actual = batch_generation._get_artman_config_filenames(
        api_config_patterns, '*', exclude_apis)
    assert expected == actual


def test_get_artman_config_filenames_comma_separated():
    api_config_patterns = ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml',
                           'test/cli/data/gapic/core/artman_${API_SHORT_NAME}.yaml']
    expected = [
        'test/cli/data/gapic/api/artman_pubsub.yaml',
        'test/cli/data/gapic/api/artman_logging.yaml',
        'test/cli/data/gapic/core/artman_core.yaml',
    ]
    actual = batch_generation._get_artman_config_filenames(
            api_config_patterns, 'pubsub,logging,core', [])
    assert expected == actual


def test_get_artman_config_filenames_list():
    api_config_patterns = ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml',
                           'test/cli/data/gapic/core/artman_${API_SHORT_NAME}.yaml']
    expected = [
        'test/cli/data/gapic/api/artman_logging.yaml',
        'test/cli/data/gapic/api/artman_longrunning.yaml',
    ]
    actual = batch_generation._get_artman_config_filenames(
            api_config_patterns, ['logging', 'longrunning'], [])
    assert expected == actual


def test_get_artman_config_filenames_list_exception():
    api_config_patterns = ['test/cli/data/gapic/api/artman_${API_SHORT_NAME}.yaml',
                           'test/cli/data/gapic/core/artman_${API_SHORT_NAME}.yaml']
    exclude_apis = [
        'test/cli/data/gapic/api/artman_longrunning.yaml',
    ]
    with pytest.raises(ValueError):
        batch_generation._get_artman_config_filenames(
            api_config_patterns, ['longrunning'], exclude_apis)


class GapicTaskFactoryTests(unittest.TestCase):
    def test_grpc_codegen_java(self):
        gtf = gapic_generation.GapicTaskFactory()
        grpc_tf = grpc_generation.GRPC_TASK_FACTORY_DICT['java']
        with mock.patch.object(grpc_tf, 'get_grpc_codegen_tasks') as get:
            tasks_ = gtf._get_grpc_codegen_tasks(language='java')
            assert tasks_ ==  get.return_value
            get.assert_called_once_with(language='java')

    def test_grpc_codegen_python(self):
        gtf = gapic_generation.GapicTaskFactory()
        grpc_tf = grpc_generation.GRPC_TASK_FACTORY_DICT['python']
        with mock.patch.object(grpc_tf, 'get_grpc_codegen_tasks') as get:
            tasks_ = gtf._get_grpc_codegen_tasks(language='python')
            assert tasks_ == get.return_value
            get.assert_called_once_with(language='python')
