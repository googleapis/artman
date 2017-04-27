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
import json
import os
import subprocess
import unittest
import uuid

from googleapiclient.http import HttpMockSequence
from googleapiclient.discovery import build_from_document
import mock

from artman.cli import main
from artman.conductors import cloudtasks_conductor


class ConductorTests(unittest.TestCase):

    _FAKE_PULL_TASKS_RESPONSE = json.dumps({
        'tasks': [
            {
                'name': 'projects/foo/locations/bar/queues/baz/tasks/fake',
                'pullTaskTarget': {
                    # Decoded string is "--api pubsub --lang python"
                    'payload': 'LS1hcGkgcHVic3ViIC0tbGFuZyBweXRob24='
                    },
                'scheduleTime': '',
                'view': 'FULL'
            }
        ]
    })

    _FAKE_ACK_TASK_RESPONSE = json.dumps({})

    _FAKE_CANCEL_TASK_LEASE_RESPONSE = json.dumps({
        'name': 'projects/foo/locations/bar/queues/baz/tasks/fake'
    })

    _FAKE_QUEUE_NAME = 'projects/foo/locations/bar/queues/baz'

    @mock.patch.object(cloudtasks_conductor, '_prepare_dir')
    @mock.patch.object(main, 'main')
    @mock.patch.object(cloudtasks_conductor, '_cleanup_tmp_dir')
    def test_start_conductor_succeed(self, cleanup_tmp_dir, cli_main,
                                     prepare_dir):
        http = HttpMockSequence([
            ({'status': '200'}, self._FAKE_PULL_TASKS_RESPONSE),
            ({'status': '200'}, self._FAKE_ACK_TASK_RESPONSE),
        ])

        client = self._create_cloudtasks_client_testing(http=http)
        prepare_dir.return_value = '/tmp', '/tmp/artman-config.yaml'
        cli_main.return_value = None
        cleanup_tmp_dir.return_value = None

        cloudtasks_conductor._pull_and_execute_tasks(
            task_client=client,
            queue_name=self._FAKE_QUEUE_NAME)
        cli_main.assert_called_once_with(
            u'--api', u'pubsub', u'--lang', u'python', '--user-config',
            '/tmp/artman-config.yaml')
        # Make sure ack is called when the task execution fails.
        cleanup_tmp_dir.assert_called_once()

    @mock.patch.object(cloudtasks_conductor, '_prepare_dir')
    @mock.patch.object(main, 'main')
    @mock.patch.object(cloudtasks_conductor, '_cleanup_tmp_dir')
    def test_start_conductor_fail(self, cleanup_tmp_dir, cli_main,
                                  prepare_dir):
        http = HttpMockSequence([
            ({'status': '200'}, self._FAKE_PULL_TASKS_RESPONSE),
            ({'status': '200'}, self._FAKE_CANCEL_TASK_LEASE_RESPONSE),
        ])
        client = self._create_cloudtasks_client_testing(http=http)
        prepare_dir.return_value = '/tmp', '/tmp/artman-config.yaml'
        cli_main.side_effect = RuntimeError('abc')

        cloudtasks_conductor._pull_and_execute_tasks(
            task_client=client,
            queue_name=self._FAKE_QUEUE_NAME)
        cli_main.assert_called_once_with(
            u'--api', u'pubsub', u'--lang', u'python', '--user-config',
            '/tmp/artman-config.yaml')
        # Make sure cancel is called when the task execution fails.
        cleanup_tmp_dir.assert_called_once()

    @mock.patch.object(os, 'makedirs')
    @mock.patch.object(uuid, 'uuid4')
    @mock.patch.object(subprocess, 'check_output')
    def test_prepare_dir(self, check_output, uuid4, os_mkdir):
        uuid4.return_value = uuid.UUID('00000000-0000-0000-0000-000000000000')
        artman_user_config_mock = mock.mock_open()
        os_mkdir.return_value = None
        check_output.return_value = b'dummy output'
        with mock.patch('io.open', artman_user_config_mock, create=True):
            cloudtasks_conductor._prepare_dir()
            os_mkdir.assert_called_once_with(
                '/tmp/artman/00000000-0000-0000-0000-000000000000')
            handler = artman_user_config_mock()
            handler.write.assert_called()

    def _create_cloudtasks_client_testing(self, http):
        with open(
            os.path.join(os.path.dirname(__file__),
                         '../../artman/conductors/cloudtasks.json'), 'r') as f:
                return build_from_document(f.read(),  http=http)
