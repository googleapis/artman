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
from artman.cli.configure import _configure_github
from artman.cli.configure import _configure_local_paths
from artman.cli.configure import _configure_publish
from artman.utils.logger import logger


class ConfigureTests(unittest.TestCase):
    @mock.patch.object(configure, '_configure_github', return_value={
        'username': 'lukesneeringer',
        'token': '1335020400',
    })
    @mock.patch.object(configure, '_configure_local_paths', return_value={
        'reporoot': '~/Code',
    })
    @mock.patch.object(configure, '_configure_publish', return_value='github')
    @mock.patch.object(io, 'open', return_value=mock.MagicMock(spec=io.IOBase))
    def test_no_user_config_gh(self, open_, publish, local_paths, github):
        open_.reset()
        configure.configure(log_level=100)

        # Assert that the YAML appears to have the correct values.
        file_handle = open_.return_value.__enter__.return_value
        assert file_handle.write.call_count == 2
        _, args, kwargs = file_handle.write.mock_calls[1]
        assert 'username: lukesneeringer' in args[0]
        assert "token: '1335020400'" in args[0]
        assert 'reporoot: ~/Code' in args[0]

    @mock.patch.object(configure, '_configure_local_paths', return_value={
        'reporoot': '~/Code',
    })
    @mock.patch.object(configure, '_configure_publish', return_value='local')
    @mock.patch.object(io, 'open', return_value=mock.MagicMock(spec=io.IOBase))
    def test_no_user_config_local(self, open_, publish, local_paths):
        open_.reset()
        configure.configure(log_level=100)

        # Assert that the YAML appears to have the correct values.
        file_handle = open_.return_value.__enter__.return_value
        assert file_handle.write.call_count == 2
        _, args, kwargs = file_handle.write.mock_calls[1]
        assert 'reporoot: ~/Code' in args[0]
        assert 'publish: local' in args[0]


@mock.patch.object(logger, 'info')
@mock.patch.object(six.moves, 'input')
class ConfigureLocalPathsTests(unittest.TestCase):
    def test_no_starting_data(self, input_, info):
        # If there is no reporoot, then helpful instructions should be logged
        # and four inputs should be requested.
        input_.side_effect = ['~/Code/', '', '', '']
        result = _configure_local_paths({})
        assert result == {'reporoot': '~/Code'}
        assert input_.call_count == 4
        assert info.call_count == 4

    def test_complete_inputs(self, input_, info):
        # Inputs for derived directories should be maintained if given.
        input_.side_effect = ['~/Code/', '~/api-client-staging', '', '']
        result = _configure_local_paths({})
        assert result == {
            'api_client_staging': '~/api-client-staging',
            'reporoot': '~/Code',
        }
        assert input_.call_count == 4
        assert info.call_count == 4

    def test_reporoot_already_set(self, input_, info):
        # We do not ask for reporoot if it is set already.
        input_.side_effect = ['', '', '']
        result = _configure_local_paths({'reporoot': '~/Code'})
        assert result == {'reporoot': '~/Code'}
        assert input_.call_count == 3
        assert info.call_count == 0


class ConfigurePublisherTests(unittest.TestCase):
    def test_valid_answer_github(self):
        with mock.patch.object(six.moves, 'input') as input_:
            input_.return_value = 'GitHub'
            result = _configure_publish()
        assert result == 'github'

    def test_invalid_answer(self):
        with mock.patch.object(six.moves, 'input') as input_:
            # Return a wrong answer the first time, and raise an exception
            # the second time (using this to verify the full recursive loop).
            input_.side_effect = ('bogus', RuntimeError)
            with pytest.raises(RuntimeError):
                _configure_publish()


class ConfigureGitHubTests(unittest.TestCase):
    @mock.patch.object(getpass, 'getpass')
    @mock.patch.object(six.moves, 'input')
    def test_github_credentials(self, input_, getpass_):
        input_.return_value = 'lukesneeringer'
        getpass_.return_value = 'I<3Meagan'
        assert _configure_github({}) == {
            'username': 'lukesneeringer',
            'token': 'I<3Meagan',
        }
