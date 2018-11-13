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
import subprocess
import unittest

import mock

import pytest

from artman.tasks import gapic_tasks


def assert_calls_equal(actual_calls, expected_calls):
    actual_call_strs = []
    for call in actual_calls:
        _, args, _ = call
        cmd = ' '.join(args[0])
        actual_call_strs.append(cmd)
    assert expected_calls == actual_call_strs


class GapicConfigGenTaskTests(unittest.TestCase):
    @mock.patch.object(subprocess, 'check_output')
    @mock.patch.object(gapic_tasks.GapicConfigGenTask, 'exec_command')
    def test_execute(self, exec_command, check_output):
        task = gapic_tasks.GapicConfigGenTask()
        result = task.execute(
            api_name='pubsub',
            api_version='v1',
            descriptor_set='/path/to/descriptor_set',
            organization_name='google-cloud',
            output_dir='/path/to/output',
            service_yaml='/path/to/service.yaml',
            toolkit_path='/path/to/toolkit',
        )
        assert result == '/'.join((
            '/path/to/output/google-cloud-pubsub-v1-config-gen',
            'google-cloud-pubsub-v1_gapic.yaml',
        ))
        expected_cmds = [
            'mkdir -p %s' % os.path.dirname(result),
            ' '.join(['java -cp',
                      '/path/to/toolkit/build/libs/gapic-generator-latest-fatjar.jar',
                      'com.google.api.codegen.GeneratorMain',
                      'GAPIC_CONFIG',
                      '--descriptor_set=/path/to/descriptor_set',
                      '--output=/path/to/output/google-cloud-pubsub-v1-config-gen/google-cloud-pubsub-v1_gapic.yaml',
                      '--service_yaml=/path/to/service.yaml',
                      ])
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)
        expected_cmds2 = [
            '/path/to/toolkit/gradlew -p /path/to/toolkit fatJar -Pclargs=',
        ]
        assert_calls_equal(check_output.mock_calls, expected_cmds2)


class DiscoGapicConfigGenTaskTests(unittest.TestCase):
    @mock.patch.object(subprocess, 'check_output')
    @mock.patch.object(gapic_tasks.DiscoGapicConfigGenTask, 'exec_command')
    def test_execute(self, exec_command, check_output):
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
        expected_cmds = [
            'mkdir -p %s' % os.path.dirname(result),
            ' '.join(['java -cp',
                      '/path/to/toolkit/build/libs/gapic-generator-latest-fatjar.jar',
                      'com.google.api.codegen.GeneratorMain',
                      'DISCOGAPIC_CONFIG',
                      '--discovery_doc=/path/to/discovery_doc.json',
                      '--output=/path/to/output/google-cloud-compute-v1-config-gen/google-cloud-compute-v1_gapic.yaml',
                      ])
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)
        expected_cmds2 = [
            '/path/to/toolkit/gradlew -p /path/to/toolkit fatJar -Pclargs='
        ]
        assert_calls_equal(check_output.mock_calls, expected_cmds2)


class GapicConfigMoveTaskTests(unittest.TestCase):
    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    def test_execute(self, exec_command):
        task = gapic_tasks.GapicConfigMoveTask()
        task.execute('/path/src', '/path/dest')
        assert exec_command.call_count == 2
        expected_cmds = [
            'mkdir -p /path',
            'cp /path/src /path/dest',
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)

    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    def test_execute_no_dest(self, exec_command):
        task = gapic_tasks.GapicConfigMoveTask()
        with pytest.raises(ValueError):
            task.execute('/path/src', None)
        assert exec_command.call_count == 0

    @mock.patch.object(gapic_tasks.GapicConfigMoveTask, 'exec_command')
    @mock.patch.object(os.path, 'exists')
    def test_execute_dest_exists(self, exists, exec_command):
        exists.return_value = True
        task = gapic_tasks.GapicConfigMoveTask()
        task.execute('/path/src', '/path/exists')
        assert exec_command.call_count == 3
        expected_cmds = [
            'mv /path/exists /path/exists.old',
            'mkdir -p /path',
            'cp /path/src /path/exists',
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)

    def test_validate(self):
        task = gapic_tasks.GapicConfigMoveTask()
        assert task.validate() == []


class GapicCodeGenTaskTests(unittest.TestCase):
    @mock.patch.object(subprocess, 'check_output')
    @mock.patch.object(gapic_tasks.GapicCodeGenTask, 'exec_command')
    def test_execute(self, exec_command, check_output):
        task = gapic_tasks.GapicCodeGenTask()
        task.execute(
            api_name='pubsub',
            api_version='v1',
            descriptor_set='/path/to/desc',
            gapic_yaml='/path/to/pubsub.yaml',
            gapic_code_dir='/path/to/output',
            language='python',
            organization_name='google-cloud',
            package_metadata_yaml='/path/to/pmy.yaml',
            service_yaml='/path/to/service.yaml',
            toolkit_path='/path/to/toolkit',
            aspect='ALL',
            generator_args='--extra_args'
        )
        expected_cmds = [
            ' '.join(['java -cp',
                      '/path/to/toolkit/build/libs/gapic-generator-latest-fatjar.jar',
                      'com.google.api.codegen.GeneratorMain LEGACY_GAPIC_AND_PACKAGE',
                      '--descriptor_set=/path/to/desc --package_yaml2=/path/to/pmy.yaml',
                      '--output=/path/to/output --language=python',
                      '--service_yaml=/path/to/service.yaml',
                      '--gapic_yaml=/path/to/pubsub.yaml',
                      '--extra_args'
                      ])
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)
        expected_cmds2 = [
            '/path/to/toolkit/gradlew -p /path/to/toolkit fatJar -Pclargs=',
        ]
        assert_calls_equal(check_output.mock_calls, expected_cmds2)


class DiscoGapicCodeGenTaskTests(unittest.TestCase):
    @mock.patch.object(subprocess, 'check_output')
    @mock.patch.object(gapic_tasks.DiscoGapicCodeGenTask, 'exec_command')
    def test_execute(self, exec_command, check_output):
        task = gapic_tasks.DiscoGapicCodeGenTask()
        task.execute(
            api_name='compute',
            api_version='v1',
            gapic_yaml='/path/to/compute.yaml',
            gapic_code_dir='/path/to/output',
            language='java',
            organization_name='google-cloud',
            package_metadata_yaml='/path/to/pmy.yaml',
            discovery_doc="compute.v1.json",
            toolkit_path='/path/to/toolkit',
            root_dir='root_dir'
        )
        expected_cmds = [
            ' '.join(['java -cp',
                      '/path/to/toolkit/build/libs/gapic-generator-latest-fatjar.jar',
                      'com.google.api.codegen.GeneratorMain LEGACY_DISCOGAPIC_AND_PACKAGE',
                      '--discovery_doc=root_dir/compute.v1.json',
                      '--package_yaml2=/path/to/pmy.yaml --output=/path/to/output',
                      '--language=java --gapic_yaml=/path/to/compute.yaml',
                      ])
        ]
        assert_calls_equal(exec_command.mock_calls, expected_cmds)
        expected_cmds2 = [
            '/path/to/toolkit/gradlew -p /path/to/toolkit fatJar -Pclargs=',
        ]
        assert_calls_equal(check_output.mock_calls, expected_cmds2)
