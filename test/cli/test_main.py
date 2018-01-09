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
from argparse import Namespace
import io
import os
import textwrap
import unittest

import mock

import pytest

from artman.cli import main
from artman.utils.logger import logger


CUR_DIR = os.path.dirname(os.path.realpath(__file__))


class ParseArgsTests(unittest.TestCase):

    def test_artifact_name_required(self):
        with pytest.raises(SystemExit):
            main.parse_args('generate')

    def test_minimal_args(self):
        flags = main.parse_args('generate', 'python_gapic')
        assert flags.config == 'artman.yaml'
        assert flags.user_config == '~/.artman/config.yaml'
        assert flags.output_dir == './artman-genfiles'
        assert flags.root_dir is ''
        assert flags.local is False
        assert flags.artifact_name == 'python_gapic'
        assert flags.image == main.ARTMAN_DOCKER_IMAGE

        flags = main.parse_args('publish', '--target=staging', 'python_gapic')
        assert flags.config == 'artman.yaml'
        assert flags.artifact_name == 'python_gapic'
        assert flags.github_username is None
        assert flags.github_token is None
        assert flags.target == 'staging'
        assert flags.verbosity is None
        assert flags.dry_run is False


class ReadUserConfigTests(unittest.TestCase):
    @mock.patch.object(logger, 'critical')
    def test_no_config(self, critical):
        flags = Namespace(user_config='/bogus/file.yaml', command='not_init')
        with pytest.raises(SystemExit):
            main.read_user_config(flags)
        critical.assert_called_once_with('No user configuration found.')

    @mock.patch.object(io, 'open')
    @mock.patch.object(os.path, 'isfile')
    def test_with_config(self, is_file, open_):
        # Create our stand-in config file.
        config_file = textwrap.dedent(u"""\
        ---
        local_paths:
          reporoot: ~/Code
        publish: local
        """)
        is_file.return_value = True
        open_.return_value = io.StringIO(config_file)

        # Get the config and test the result.
        flags = Namespace(user_config='/bogus/file.yaml', command='not_init')
        user_config = main.read_user_config(flags)
        assert user_config == {
            'local_paths': {'reporoot': '~/Code'},
            'publish': 'local',
        }


class NormalizeFlagTests(unittest.TestCase):
    CURDIR = os.path.realpath(os.path.dirname(__file__))

    def setUp(self):
        self.flags = Namespace(
            config=os.path.join(CUR_DIR, 'data', 'artman_test.yaml'),
            root_dir=os.path.join(CUR_DIR, 'data'),
            subcommand='generate',
            github_username='test', github_token='token',
            artifact_name='python_gapic',
            output_dir='./artman-genfiles',
            dry_run=False,
            local_repo_dir=None,
        )
        self.user_config = {
            'local_paths': {'reporoot': os.path.realpath('..')},
            'publish': 'local',
        }

    def test_basic_args(self):
        name, args = main.normalize_flags(self.flags, self.user_config)
        assert name == 'GapicClientPipeline'
        assert args['common_protos_yaml'].endswith('common_protos.yaml')
        assert args['desc_proto_path'][0].endswith('google/iam/v1')
        assert args['gapic_api_yaml'][0].endswith('test_gapic.yaml')
        assert args['gapic_language_yaml'][0].endswith('python_gapic.yaml')
        assert args['local_paths']
        assert 'github' not in args
        assert args['language'] == 'python'
        assert args['publish'] == 'noop'

    def test_github_credentials(self):
        self.flags.target = 'github'
        self.flags.subcommand = 'publish'
        name, args = main.normalize_flags(self.flags, self.user_config)
        assert args['publish'] == 'github'
        assert args['github']['username'] == 'test'
        assert args['github']['token'] == 'token'
