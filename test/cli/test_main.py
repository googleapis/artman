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
import json
import logging
import os
import textwrap
import time
import unittest

import gcloud

import mock

import pytest

from artman.cli import main
from artman.utils.logger import logger


class ParseArgsTests(unittest.TestCase):
    def test_no_args(self):
        with pytest.raises(SystemExit):
            main.parse_args()

    def test_api_or_config_required(self):
        with pytest.raises(SystemExit):
            main.parse_args('--language', 'python')

    def test_api_or_config_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            main.parse_args('--api', 'pubsub', '--language', 'python',
                            '--config' '../googleapis/gapic/artman_pubsub.yml')

    def test_minimal_args(self):
        flags = main.parse_args('--language', 'python',
                                '--api', 'pubsub')
        assert flags.pipeline_name == 'GapicClientPipeline'
        assert flags.pipeline_kwargs == '{}'
        assert flags.api == 'pubsub'
        assert flags.user_config == '~/.artman/config.yaml'
        assert flags.googleapis is None
        assert flags.remote is False
        assert flags.language == 'python'
        assert flags.github_username is None
        assert flags.github_token is None
        assert flags.publish is None
        assert flags.target is None
        assert flags.config is ''
        assert flags.verbosity is None


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
            api='pubsub', config=None,
            github_username='lukesneeringer', github_token='1335020400',
            googleapis='%s/data' % self.CURDIR, language='python',
            pipeline_name='GapicClientPipeline', pipeline_kwargs='{}',
            publish='local', remote=False, target='staging', verbosity=60,
        )
        self.user_config = {
            'local_paths': {'reporoot': os.path.realpath('..')},
            'publish': 'local',
        }

    def test_basic_args(self):
        name, args, env = main.normalize_flags(self.flags, self.user_config)
        assert name == 'GapicClientPipeline'
        assert args['common_protos_yaml'].endswith('common_protos.yaml')
        assert args['desc_proto_path'][0].endswith('google/iam/v1')
        assert args['gapic_api_yaml'][0].endswith('pubsub_gapic.yaml')
        assert args['gapic_language_yaml'][0].endswith('python_gapic.yaml')
        assert args['local_paths']
        assert 'github' not in args
        assert args['language'] == 'python'
        assert args['publish'] == 'local'
        assert env is None

    def test_no_language(self):
        self.flags.language = None
        with pytest.raises(SystemExit):
            main.normalize_flags(self.flags, self.user_config)

    def test_no_language_config_pipeline(self):
        self.flags.pipeline_name = 'GapicConfigPipeline'
        self.flags.language = None
        name, args, env = main.normalize_flags(self.flags, self.user_config)
        assert name == 'GapicConfigPipeline'
        assert 'language' not in args

    def test_github_credentials(self):
        self.flags.publish = 'github'
        name, args, env = main.normalize_flags(self.flags, self.user_config)
        assert args['publish'] == 'github'
        assert args['github']['username'] == 'lukesneeringer'
        assert args['github']['token'] == '1335020400'

    def test_pipeline_kwargs(self):
        self.flags.pipeline_kwargs = json.dumps({
            'foo': 'bar',
            'spam': 'eggs',
        })
        with mock.patch.object(logger, 'warn') as warn:
            _, args, _ = main.normalize_flags(self.flags, self.user_config)
            warn.assert_called_once()
        assert args['foo'] == 'bar'
        assert args['spam'] == 'eggs'

    def test_remote(self):
        self.flags.remote = True
        _, args, env = main.normalize_flags(self.flags, self.user_config)
        assert args['local_paths']['reporoot'].startswith('/tmp/artman/')
        assert env == 'remote'

    def test_explicit_config(self):
        self.flags.api = None
        self.flags.config = ','.join([
            '%s/data/gapic/api/artman_pubsub.yaml' % self.CURDIR,
            '%s/data/gapic/lang/common.yaml' % self.CURDIR,
        ])
        _, args, _ = main.normalize_flags(self.flags, self.user_config)
        assert args['gapic_api_yaml'][0].endswith('pubsub_gapic.yaml')
        assert args['gapic_language_yaml'][0].endswith('python_gapic.yaml')


class PrintLogTests(unittest.TestCase):
    @mock.patch.object(gcloud.logging, 'Client')
    @mock.patch.object(logger, 'error')
    @mock.patch.object(time, 'sleep')
    def test_print_log(self, sleep, error, client):
        client().logger().list_entries.return_value = [
            (Namespace(payload='foo'), Namespace(payload='bar')),
            'token',
        ]
        main._print_log('00000000')
        assert error.call_count == 2
        assert error.mock_calls[0][1][0] == 'foo'
        assert error.mock_calls[1][1][0] == 'bar'
        sleep.assert_called_once_with(30)
