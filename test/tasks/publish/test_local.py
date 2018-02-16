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

from artman.tasks.publish import local
from artman.utils.logger import logger


class LocalStagingTests(unittest.TestCase):
    @mock.patch.object(local.LocalStagingTask, 'exec_command')
    @mock.patch('os.path.isdir')
    def test_execute(self, is_dir, exec_command):
        is_dir.return_value = True
        # Run the task.
        task = local.LocalStagingTask()
        task.execute(
            gapic_code_dir=os.path.expanduser('~/foo/bar'),
            git_repo={
                'paths': ['pubsub'],
                'location': 'api-client-staging.git',
            },
            local_repo_dir='/path/to/local/repo',
            output_dir='/path/to/output',
        )

        # Ensure we executed the commands we expect.
        assert exec_command.call_count == 4
        _, rm_cmd, _ = exec_command.mock_calls[0]
        assert rm_cmd[0] == ['rm', '-rf', '/path/to/local/repo/pubsub']
        _, cp_cmd, _ = exec_command.mock_calls[1]
        assert cp_cmd[0] == ['cp', '-rf', os.path.expanduser('~/foo/bar'),
            '/path/to/local/repo/pubsub',
        ]
        _, rm_cmd_2, _ = exec_command.mock_calls[2]
        assert rm_cmd_2[0] == ['rm', '-rf', os.path.expanduser('~/foo/bar')]
        _, rm_cmd_3, _ = exec_command.mock_calls[3]
        assert rm_cmd_3[0] == ['rm', '-rf', '/path/to/output']

    @mock.patch.object(local.LocalStagingTask, 'exec_command')
    @mock.patch('os.path.isdir')
    def test_execute_git_location_without_dot_git(self, is_dir, exec_command):
        is_dir.return_value = True
        # Run the task.
        # This time, send a location that does not end in ".git" (as an
        # https location would not).
        task = local.LocalStagingTask()
        task.execute(
            gapic_code_dir=os.path.expanduser('~/foo/bar'),
            git_repo={
                'paths': ['pubsub'],
                'location': 'api-client-staging',
            },
            local_repo_dir='/path/to/local/repo',
            output_dir='/path/to/output',
        )

        # Ensure that the correct path is still determined.
        for _, args, _ in exec_command.mock_calls[0:1]:
            assert '/path/to/local/repo/pubsub' in args[0]

    @mock.patch.object(local.LocalStagingTask, 'exec_command')
    @mock.patch('os.path.isdir')
    def test_execute_output_dir_parent_of_gapic_dest(self, is_dir, exec_command):
        is_dir.return_value = True
        # Run the task.
        task = local.LocalStagingTask()
        task.execute(
            gapic_code_dir=os.path.expanduser('~/foo/bar'),
            git_repo={
                'paths': ['pubsub'],
                'location': 'api-client-staging.git',
            },
            local_repo_dir='/path/to/local/repo',
            output_dir='/path/to',
        )

        # Ensure we executed the commands we expect.
        assert exec_command.call_count == 3
        _, rm_cmd, _ = exec_command.mock_calls[0]
        assert rm_cmd[0] == ['rm', '-rf', '/path/to/local/repo/pubsub']
        _, cp_cmd, _ = exec_command.mock_calls[1]
        assert cp_cmd[0] == ['cp', '-rf', os.path.expanduser('~/foo/bar'),
            '/path/to/local/repo/pubsub',
        ]
        _, rm_cmd_2, _ = exec_command.mock_calls[2]
        assert rm_cmd_2[0] == ['rm', '-rf', os.path.expanduser('~/foo/bar')]

    @mock.patch.object(local.LocalStagingTask, 'exec_command')
    @mock.patch.object(logger, 'success')
    @mock.patch('os.path.isdir')
    def test_execute_with_grpc(self, is_dir, success, exec_command):
        is_dir.return_value = True
        # Run the task, this time with a registered grpc location.
        task = local.LocalStagingTask()
        task.execute(
            gapic_code_dir='/path/to/gapic',
            grpc_code_dir='/path/to/grpc',
            git_repo={
                'paths': [
                    'gapic/pubsub',
                    {'artifact': 'grpc', 'dest': 'grpc/pubsub'},
                ],
                'location': 'git@github.com:googleapis/api-client-staging.git',
            },
            local_repo_dir='/path/to/local/repo',
            output_dir='/tmp/out',
        )

        # Establish the commands we expect to have been called.
        expected_commands = (
            'rm -rf /path/to/local/repo/gapic/pubsub',
            'cp -rf /path/to/gapic /path/to/local/repo/gapic/pubsub',
            'rm -rf /path/to/local/repo/grpc/pubsub',
            'cp -rf /path/to/grpc /path/to/local/repo/grpc/pubsub',
            'rm -rf /path/to/gapic',
            'rm -rf /path/to/grpc',
            'rm -rf /tmp/out',
        )
        assert len(exec_command.mock_calls) == len(expected_commands)
        for cmd, call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = call
            assert ' '.join(args[0]) == cmd

        # Establish the expected log entires.
        expected_messages = (
            'Code generated: /path/to/local/repo/gapic/pubsub',
            'Code generated: /path/to/local/repo/grpc/pubsub',
        )
        assert len(success.mock_calls) == len(expected_messages)
        for msg, call in zip(expected_messages, success.mock_calls):
            _, args, _ = call
            assert args[0] == msg

    @mock.patch.object(local.LocalStagingTask, 'exec_command')
    @mock.patch.object(logger, 'success')
    @mock.patch('os.path.isdir')
    def test_execute_without_api_client_staging_user_config(
        self, is_dir, success, exec_command):
        is_dir.return_value = True
        # Run the task, this time with a registered grpc location.
        task = local.LocalStagingTask()
        task.execute(
            gapic_code_dir='/path/to/gapic',
            git_repo={
                'paths': [
                    'gapic/pubsub'
                ],
                'location': 'git@github.com:googleapis/api-client-staging.git',
            },
            output_dir='/tmp/out',
        )

        # Establish the commands we expect to have been called.
        expected_commands = (
            'git clone https://github.com/googleapis/api-client-staging.git '
            '/tmp/out/api-client-staging',
            'rm -rf /tmp/out/api-client-staging/gapic/pubsub',
            'cp -rf /path/to/gapic /tmp/out/api-client-staging/gapic/pubsub',
            'rm -rf /path/to/gapic',
        )
        assert len(exec_command.mock_calls) == len(expected_commands)
        for cmd, call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = call
            assert ' '.join(args[0]) == cmd

        # Establish the expected log entires.
        expected_messages = (
            'Code generated: /tmp/out/api-client-staging/gapic/pubsub',
        )
        assert len(success.mock_calls) == len(expected_messages)
        for msg, call in zip(expected_messages, success.mock_calls):
            _, args, _ = call
            assert args[0] == msg
