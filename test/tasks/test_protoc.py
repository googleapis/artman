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
import unittest

import mock

import pytest

from artman.tasks import protoc_tasks
from artman.utils import protoc_utils


class JavaProtoCopyTaskTests(unittest.TestCase):
    @mock.patch.object(protoc_tasks.JavaProtoCopyTask, 'exec_command')
    def test_execute(self, exec_command):
        src_proto_path = ['test/tasks/data/googleapis/google/pubsub/v1']
        grpc_code_dir = 'grpc_code_dir'
        task = protoc_tasks.JavaProtoCopyTask()
        task.execute(src_proto_path, grpc_code_dir)
        assert exec_command.call_count == 2
        expected_cmds = (
            'mkdir -p grpc_code_dir/src/main/proto/google/pubsub/v1',
            'cp test/tasks/data/googleapis/google/pubsub/v1/pubsub.proto '
            + 'grpc_code_dir/src/main/proto/google/pubsub/v1/pubsub.proto',
        )
        for call, expected in zip(exec_command.mock_calls, expected_cmds):
            _, args, _ = call
            assert ' '.join(args[0]) == expected

    @mock.patch.object(protoc_tasks.JavaProtoCopyTask, 'exec_command')
    def test_execute_bad_src_path(self, exec_command):
        src_proto_path = ['test/tasks/data/googleapis/groogle/pubsub/v1']
        grpc_code_dir = 'grpc_code_dir'
        task = protoc_tasks.JavaProtoCopyTask()
        with pytest.raises(ValueError):
            task.execute(src_proto_path, grpc_code_dir)
        assert exec_command.call_count == 0


def test_find_google_dir_index():
    expected = [
        ('google', 0),
        ('google/path', 0),
        ('path/google', 5),
        ('path/google/more', 5),
        ('path\\google\\more', 5),
        ('google/google', 7),
        ('googlea/google/googleb/cgoogle/Google', 8),
    ]
    for path, index in expected:
        assert protoc_utils.find_google_dir_index(path) == index

    failing = [
        '',
        'any/old/path',
        'any\\old\\path',
        'Google',
        'agoogle/googleb',
    ]
    for path in failing:
        with pytest.raises(ValueError):
            protoc_utils.find_google_dir_index(path)


def test_find_protos_no_exclusion():
    expected = [
        'test/fake-repos/fake-proto/fake.proto',
        'test/fake-repos/fake-proto/excluded/excluded.proto'
    ]
    src_proto_paths = [
        'test/fake-repos/fake-proto'
    ]
    assert  list(protoc_utils.find_protos(src_proto_paths, [])) == expected


def test_find_protos_with_exclusion():
    expected = [
        'test/fake-repos/fake-proto/fake.proto'
    ]
    src_proto_paths = [
        'test/fake-repos/fake-proto'
    ]
    excluded_proto_paths = [
        'test/fake-repos/fake-proto/excluded'
    ]
    assert list(protoc_utils.find_protos(
        src_proto_paths, excluded_proto_paths)) == expected

def test_find_protos_listing_filename():
    expected = [
        'test/fake-repos/fake-proto/fake.proto',
    ]
    src_proto_paths = [
        'test/fake-repos/fake-proto/fake.proto',
    ]
    assert list(protoc_utils.find_protos(src_proto_paths, [])) == expected
