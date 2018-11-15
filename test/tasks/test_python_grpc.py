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

import mock
import pytest

from artman.tasks import python_grpc_tasks


def test_get_subdir_path():
    task = python_grpc_tasks.PythonMoveProtosTask()
    with mock.patch.object(os, 'walk') as walk:
        walk.return_value = (
            ('foo', ['bar'], []),
            ('foo/bar', ['proto'], []),
            ('foo/bar/proto', [], ['file_pb2.py']),
        )
        assert task._get_subdir_path('.', 'proto') == 'foo/bar'


def test_get_subdir_path_not_found():
    task = python_grpc_tasks.PythonMoveProtosTask()
    with mock.patch.object(os, 'walk') as walk:
        walk.return_value = (
            ('foo', ['bar'], []),
        )
        with pytest.raises(RuntimeError):
            task._get_subdir_path('.', 'proto')


def test_move_protos():
    task = python_grpc_tasks.PythonMoveProtosTask()
    with mock.patch.object(task, 'exec_command') as exec_command:
        with mock.patch.object(task, '_get_proto_path') as _gpp:
            _gpp.side_effect = ('grpc_path/foo/bar/proto',)
            with mock.patch.object(task, '_get_subdir_path') as _gsp:
                _gsp.side_effect = (
                    'gapic_path/foo/bar/',
                )
                assert task.execute('grpc_path', 'gapic_path') == {
                    'grpc_code_dir': None,
                }
                # Inspect the calls to _get_proto_path to make sure we are looking
                # for the paths we expect.
                assert _gpp.call_count == 1
                proto_call = _gpp.mock_calls[0]
                assert proto_call[1] == ('grpc_path',)
                # Inspect the calls to _get_subdir_path to make sure we are looking
                # for the paths we expect.
                assert _gsp.call_count == 1
                gapic_call = _gsp.mock_calls[0]
                assert gapic_call[1] == ('gapic_path/google', 'gapic')

        # Ensure that the correct commands ran.
        assert exec_command.call_count == 3
        mv = exec_command.mock_calls[0]
        touch = exec_command.mock_calls[1]
        rm = exec_command.mock_calls[2]
        assert mv[1] == ([
            'mv',
            'grpc_path/foo/bar/proto',
            'gapic_path/foo/bar/proto',
        ],)
        assert touch[1] == (['touch', 'gapic_path/foo/bar/proto/__init__.py'],)
        assert rm[1] == (['rm', '-rf', 'grpc_path'],)
