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
import argparse
import os
import unittest

import pytest

from artman.cli import support


class ParseGitHubCredentialsTests(unittest.TestCase):
    def test_read_from_config_file(self):
        user_config = {'username': 'foo', 'token': 'bar'}
        flags = argparse.Namespace(github_username=None, github_token=None)
        result = support.parse_github_credentials(user_config, flags)
        assert result == user_config

    def test_read_from_argv(self):
        user_config = {}
        flags = argparse.Namespace(github_username='spam', github_token='eggs')
        result = support.parse_github_credentials(user_config, flags)
        assert result == {'username': 'spam', 'token': 'eggs'}

    def test_read_from_config_file_and_argv(self):
        # If we get values both in the config file and in sys.argv, the latter
        # should win.
        user_config = {'username': 'foo', 'token': 'bar'}
        flags = argparse.Namespace(github_username='spam', github_token='eggs')
        result = support.parse_github_credentials(user_config, flags)
        assert result == {'username': 'spam', 'token': 'eggs'}

    def test_no_credentials_error(self):
        user_config = {}
        flags = argparse.Namespace(github_username=None, github_token=None)
        with pytest.raises(SystemExit):
            support.parse_github_credentials(user_config, flags)


class ParseLocalPathsTests(unittest.TestCase):
    def test_normal(self):
        user_config = {'local_paths': {'reporoot': '~/Code'}}
        result = support.parse_local_paths(user_config, None)
        base = os.path.expanduser('~/Code')
        assert result == {
            'reporoot': base,
            'artman': '{}/artman'.format(base),
            'api_client_staging': '{}/api-client-staging'.format(base),
            'googleapis': '{}/googleapis'.format(base),
            'toolkit': '{}/toolkit'.format(base),
        }

    def test_googleapis_flag(self):
        user_config = {'local_paths': {'reporoot': '~/Code'}}
        result = support.parse_local_paths(user_config, '/path/to/googleapis')
        base = os.path.expanduser('~/Code')
        assert result['googleapis'] == '/path/to/googleapis'


class ResolveTests(unittest.TestCase):
    def test_neither_set(self):
        user_config = {}
        flags = argparse.Namespace()
        result = support.resolve('foo', user_config, flags, default=42)
        assert result == 42

    def test_neither_set_no_default(self):
        user_config = {}
        flags = argparse.Namespace()
        result = support.resolve('foo', user_config, flags)
        assert result is None

    def test_user_config_only_set(self):
        user_config = {'bar': 3}
        flags = argparse.Namespace(bar=None)
        result = support.resolve('bar', user_config, flags, default=42)
        assert result == 3

    def test_flag_only_set(self):
        user_config = {}
        flags = argparse.Namespace(baz=9)
        result = support.resolve('baz', user_config, flags, default=42)
        assert result == 9

    def test_both_set(self):
        user_config = {'bacon': 'gross'}
        flags = argparse.Namespace(bacon='yummy!')
        result = support.resolve('bacon', user_config, flags, default='meh')
        assert result == 'yummy!'


class SelectGitRepoTests(unittest.TestCase):
    def setUp(self):
        self.git_repos = {
            'my_repo': {
                'location': 'my_repo_url.git',
            },
            'staging': {
                'location': 'my_staging_repo.git'
            },
            'my_default_repo': {
                'location': 'my_default_repo_url.git',
                'default': True
            }
        }

    def test_target_repo(self):
        result = support.select_git_repo(self.git_repos, 'my_repo')
        assert result['location'] == 'my_repo_url.git'

    def test_default_repo(self):
        result = support.select_git_repo(self.git_repos, None)
        assert result['location'] == 'my_default_repo_url.git'

    def test_no_default_repo(self):
        del self.git_repos['my_default_repo']['default']
        result = support.select_git_repo(self.git_repos, None)
        assert result['location'] == 'my_staging_repo.git'

    def test_missing_repo(self):
        with self.assertRaises(SystemExit):
            support.select_git_repo(self.git_repos, 'not_a_repo')
