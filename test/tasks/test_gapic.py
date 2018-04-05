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

import pytest

from artman.tasks import gapic_tasks
from artman.tasks.requirements import gapic_requirements


class GapicConfigGenTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.GapicConfigGenTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.GapicConfigGenTask()
        result = task.execute(
            api_name='pubsub',
            api_version='v1',
            descriptor_set='/path/to/descriptor_set',
            organization_name='google-cloud',
            output_dir='/path/to/output',
            service_yaml=['/path/to/service.yaml'],
            toolkit_path='/path/to/toolkit',
        )
        assert result == '/'.join((
            '/path/to/output/google-cloud-pubsub-v1-config-gen',
            'google-cloud-pubsub-v1_gapic.yaml',
        ))
        expected_cmds = (
            'mkdir -p %s' % os.path.dirname(result),
            ''.join((
                '/path/to/toolkit/gradlew -p /path/to/toolkit runConfigGen '
                '-Pclargs=--descriptor_set=/path/to/descriptor_set,',
                '--output=/path/to/output/google-cloud-pubsub-v1-config-gen/',
                'google-cloud-pubsub-v1_gapic.yaml,--service_yaml=',
                '/path/to/service.yaml',
            )),
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            cmd = ' '.join(args[0])
            assert cmd == expected

    def test_validate(self):
        task = gapic_tasks.GapicConfigGenTask()
        assert task.validate() == [gapic_requirements.ConfigGenRequirements]


class DiscoGapicConfigGenTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.DiscoGapicConfigGenTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.DiscoGapicConfigGenTask()
        result = task.execute(
            api_name='compute',
            api_version='v1',
            organization_name='google-cloud',
            output_dir='/path/to/output',
            discovery_doc='/path/to/discovery_doc.json',
            toolkit_path='/path/to/toolkit',
        )
        assert result == '/'.join((
            '/path/to/output/google-cloud-compute-v1-config-gen',
            'google-cloud-compute-v1_gapic.yaml',
        ))
        expected_cmds = (
            'mkdir -p %s' % os.path.dirname(result),
            ''.join((
                '/path/to/toolkit/gradlew -p /path/to/toolkit runDiscoConfigGen '
                '-Pclargs=',
                '--discovery_doc=',
                '/path/to/discovery_doc.json,'
                '--output=/path/to/output/google-cloud-compute-v1-config-gen/',
                'google-cloud-compute-v1_gapic.yaml',
            )),
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            cmd = ' '.join(args[0])
            assert cmd == expected

    def test_validate(self):
        task = gapic_tasks.DiscoGapicConfigGenTask()
        assert task.validate() == [gapic_requirements.ConfigGenRequirements]


class GapicConfigMoveTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.GapicConfigMoveTask()
        task.execute('/path/src', ['/path/dest'])
        assert exec_command.call_count == 2
        expected_cmds = (
            'mkdir -p /path',
            'cp /path/src /path/dest',
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            assert ' '.join(args[0]) == expected

    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    def test_execute_no_dest(self, exec_command):
        task = gapic_tasks.GapicConfigMoveTask()
        with pytest.raises(ValueError):
            task.execute('/path/src', [])
        assert exec_command.call_count == 0

    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    def test_execute_multi_dest(self, exec_command):
        task = gapic_tasks.GapicConfigMoveTask()
        with pytest.raises(ValueError):
            task.execute('/path/src', ['/path/one', '/path/two'])
        assert exec_command.call_count == 0

    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    @mock.patch.object(os.path, 'exists')
    def test_execute_dest_exists(self, exists, exec_command):
        exists.return_value = True
        task = gapic_tasks.GapicConfigMoveTask()
        task.execute('/path/src', ['/path/exists'])
        assert exec_command.call_count == 3
        expected_cmds = (
            'mv /path/exists /path/exists.old',
            'mkdir -p /path',
            'cp /path/src /path/exists',
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            assert ' '.join(args[0]) == expected

    def test_validate(self):
        task = gapic_tasks.GapicConfigMoveTask()
        assert task.validate() == []


class GapicCodeGenTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.GapicCodeGenTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.GapicCodeGenTask()
        task.execute(
            api_name='pubsub',
            api_version='v1',
            descriptor_set='/path/to/desc',
            gapic_api_yaml='pubsub.yaml',
            gapic_code_dir='api-client-staging/generated/python',
            gapic_language_yaml='python.yaml',
            language='python',
            organization_name='google-cloud',
            package_metadata_yaml='pmy.yaml',
            service_yaml='service.yaml',
            toolkit_path='/path/to/toolkit'
        )
        expected_cmds = (
            '/path/to/toolkit/gradlew -p /path/to/toolkit runCodeGen',
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            assert expected in ' '.join(args[0])

    def test_validate(self):
        task = gapic_tasks.GapicCodeGenTask()
        assert task.validate() == [gapic_requirements.GapicRequirements]


class DiscoGapicCodeGenTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.DiscoGapicCodeGenTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.DiscoGapicCodeGenTask()
        task.execute(
            api_name='compute',
            api_version='v1',
            gapic_api_yaml='compute.yaml',
            gapic_code_dir='api-client-staging/generated/java',
            discogapic_language_yaml='java.yaml',
            language='java',
            organization_name='google-cloud',
            package_metadata_yaml='pmy.yaml',
            discovery_doc="compute.v1.json",
            toolkit_path='/path/to/toolkit'
        )
        expected_cmds = (
            '/path/to/toolkit/gradlew -p /path/to/toolkit runDiscoCodeGen',
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            assert expected in ' '.join(args[0])

    def test_validate(self):
        task = gapic_tasks.DiscoGapicCodeGenTask()
        assert task.validate() == [gapic_requirements.GapicRequirements]


class GapicPackmanTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.GapicPackmanTask, 'run_packman')
    def test_execute(self, run_packman):
        task = gapic_tasks.GapicPackmanTask()
        result = task.execute('python', 'pubsub', 'v1', 'gcloud', '/gapic/cd')
        assert result == '/gapic/cd'
        run_packman.assert_called_once_with('python', 'gcloud/pubsub/v1',
            '--gax_dir=/gapic/cd',
            '--template_root=templates/gax',
        )

    @mock.patch.object(gapic_tasks.GapicPackmanTask, 'run_packman')
    def test_execute_skip_packman(self, run_packman):
        task = gapic_tasks.GapicPackmanTask()
        result = task.execute('python', 'pubsub', 'v1', 'gcloud', '/gapic/cd',
            skip_packman=True,
        )
        assert result == '/gapic/cd'
        assert run_packman.call_count == 0
