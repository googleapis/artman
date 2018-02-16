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
from artman.cli.configure import _configure_github_config
from artman.cli.configure import _configure_local_config
from artman.config.proto.user_config_pb2 import LocalConfig, GitHubConfig
from artman.utils.logger import logger


class ConfigureTests(unittest.TestCase):
    @mock.patch.object(configure, '_configure_github_config')
    @mock.patch.object(configure, '_configure_local_config')
    @mock.patch.object(configure, '_write_pb_to_yaml')
    def test_no_user_config_gh(self, write_pb_to_yaml, configure_local_config,
                               configure_github_config):
        github_config = GitHubConfig()
        github_config.username = 'test'
        github_config.token = 'DUMMYTOKEN'
        local_config = LocalConfig()
        local_config.toolkit = '/toolkit'
        configure_github_config.return_value = github_config
        configure_local_config.return_value = local_config

        configure.configure(log_level=100)
        _, args, kwargs = write_pb_to_yaml.mock_calls[0]
        user_config = args[0]
        assert 'test' == user_config.github.username
        assert 'DUMMYTOKEN' == user_config.github.token
        assert '/toolkit' == user_config.local.toolkit


@mock.patch.object(six.moves, 'input')
class ConfigureLocalPathsTests(unittest.TestCase):
    def test_configure_local_config(self, input_):
        input_.side_effect = ['/toolkit']
        result = _configure_local_config()
        assert '/toolkit' == result.toolkit
        assert 1 == input_.call_count


class ConfigureGitHubTests(unittest.TestCase):
    @mock.patch.object(logger, 'info')
    @mock.patch.object(getpass, 'getpass')
    @mock.patch.object(six.moves, 'input')
    def test_github_credentials(self, input_, getpass_, info):
        input_.return_value = 'lukesneeringer'
        getpass_.return_value = 'I<3Meagan'
        result = _configure_github_config()
        assert 'lukesneeringer' == result.username
        assert 'I<3Meagan' == result.token
        assert 1 == input_.call_count
        assert 1 == getpass_.call_count
        assert 3 == info.call_count
