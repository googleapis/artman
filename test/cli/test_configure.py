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
import getpass
import io
import unittest

import mock

import pytest

import six

from artman.cli import configure
from artman.cli.configure import _configure_local_config
from artman.config.proto.user_config_pb2 import LocalConfig


class ConfigureTests(unittest.TestCase):
    @mock.patch.object(configure, '_configure_local_config')
    @mock.patch.object(configure, '_write_pb_to_yaml')
    def test_no_user_config_gh(self, write_pb_to_yaml, configure_local_config):
        local_config = LocalConfig()
        local_config.toolkit = '/toolkit'
        configure_local_config.return_value = local_config

        configure.configure(log_level=100)
        _, args, kwargs = write_pb_to_yaml.mock_calls[0]
        user_config = args[0]
        assert '/toolkit' == user_config.local.toolkit


@mock.patch.object(six.moves, 'input')
class ConfigureLocalPathsTests(unittest.TestCase):
    def test_configure_local_config(self, input_):
        input_.side_effect = ['/toolkit']
        result = _configure_local_config()
        assert '/toolkit' == result.toolkit
        assert 1 == input_.call_count
