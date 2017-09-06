# Copyright 2016 Google Inc. All Rights Reserved.
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

import io
import mock
import os
import unittest

from artman.tasks import python_grpc_tasks


class PythonPackageChangeTest(unittest.TestCase):

    _TASK = python_grpc_tasks.PythonChangePackageTask()
    _TASK._organization_name = 'google'

    _PROTO_FILE = [
        '# Comment line\n',
        'package google.service.v1;\n',
        'import "google/service/v1/a.proto";\n',
        'import "google/cloud/otherapi/v3/b.proto";\n',
        'import "google/common/common_proto.proto";\n',
        'Some other text referencing to google.service.v1\n']

    def test__extract_base_dirs(self):
        mock_proto = mock.mock_open()
        mock_proto.return_value.__iter__ = lambda _: iter(self._PROTO_FILE)
        with mock.patch.object(io, 'open', mock_proto):
            base_dirs = self._TASK._extract_base_dirs(
                os.path.join('a', 'test', 'path', 'to', 'google', 'service',
                             'v1', 'a.proto'))
            repeated_base_dirs = self._TASK._extract_base_dirs(
                os.path.join('home', 'foo', 'workspaces', 'google', 'some',
                             'v1', 'googleapis', 'google', 'service', 'v1',
                             'a.proto'))
        expected = os.path.join('google', 'service', 'v1')
        self.assertEqual(base_dirs, expected)
        self.assertEqual(repeated_base_dirs, expected)

    def test__transfom(self):
        # Simple package transformations with arbitrary separator
        self.assertEqual(self._TASK._transform('google.service.v1', '.', []),
                         'google.service_v1.proto')
        self.assertEqual(
            self._TASK._transform('google.service.v1alpha', '.', []),
            'google.service_v1alpha.proto',
        )
        self.assertEqual(self._TASK._transform('google/other/v1', '/', []),
                         'google/other_v1/proto')
        self.assertEqual(self._TASK._transform('google$service', '$', []),
                         'google$service')

        # Don't transform common protos
        self.assertEqual(
            self._TASK._transform('google/common', '/', ['google.common']),
            'google/common')
        self.assertEqual(
            self._TASK._transform(
                'google/uncommon/v1',
                '/',
                ['google.common'],
            ),
            'google/uncommon_v1/proto',
        )

        # Don't transform non-Google protos
        self.assertEqual(
            self._TASK._transform('my_custom/path', '/', ['']),
            'my_custom/path')

    def test__copy_proto(self):
        mock_proto = mock.mock_open()
        mock_proto.return_value.__iter__ = lambda _: iter(self._PROTO_FILE)
        with mock.patch.object(io, 'open', mock_proto):
            self._TASK._copy_proto('foo', 'bar', ['google.common'])
        expected_writes = [
            mock.call('# Comment line\n'),
            mock.call('package google.service.v1;\n'),
            mock.call('import "google/service_v1/proto/a.proto";\n'),
            mock.call('import "google/cloud/otherapi_v3/proto/b.proto";\n'),
            mock.call('import "google/common/common_proto.proto";\n'),
            mock.call('Some other text referencing to google.service.v1\n')]

        mock_proto().write.assert_has_calls(expected_writes)
