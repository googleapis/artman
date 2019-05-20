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
import subprocess

import mock

import pytest

from artman.tasks import format_tasks
from artman.utils import task_utils


class JavaFormatTaskTests(unittest.TestCase):
    @mock.patch.object(format_tasks.JavaFormatTask, 'exec_command')
    @mock.patch.object(task_utils, 'get_java_tool_path')
    @mock.patch.object(os, 'walk')
    def test_execute(self, walk, gradle_output, exec_command):
        gradle_output.return_value = '/path/to/gapic'
        walk.return_value = (['/path', (), ('f1.java', 'f2.java', 'f3.py')],)
        task = format_tasks.JavaFormatTask()
        task.execute('/path/to/gapic', '/path/to/toolkit')
        exec_command.assert_called_once_with([
            'java', '-jar', '/path/to/gapic', '--replace',
            '/path/f1.java', '/path/f2.java',
        ])

    def test_validate(self):
        task = format_tasks.JavaFormatTask()
        assert task.validate() == []


class GoFormatTaskTests(unittest.TestCase):
    @mock.patch.object(format_tasks.GoFormatTask, 'exec_command')
    def test_execute(self, exec_command):
        task = format_tasks.GoFormatTask()
        task.execute('/path/to/gapic')
        exec_command.assert_called_once_with(['gofmt', '-w', '/path/to/gapic'])


class PhpFormatTaskTests(unittest.TestCase):
    @mock.patch.object(subprocess, 'call')
    def test_execute(self, call):
        call.return_value = 0
        task = format_tasks.PhpFormatTask()
        task.execute('/path/to/gapic')
        expected_cmds = (
            'php-cs-fixer fix --rules=@Symfony,-phpdoc_annotation_without_dot '
            '/path/to/gapic',
            'php-cs-fixer fix --rules={"phpdoc_no_alias_tag" : {'
            '"replacements" : {"var" : "type"}}} /path/to/gapic',
            'phpcbf --standard=PSR2 --no-patch /path/to/gapic',
        )
        assert call.call_count == len(expected_cmds)
        for c, expected in zip(call.mock_calls, expected_cmds):
            _, args, _ = c
            assert ' '.join(args[0]) == expected
