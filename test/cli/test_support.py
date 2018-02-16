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
from artman.config.proto.user_config_pb2 import GitHubConfig


class ParseGitHubCredentialsTests(unittest.TestCase):
    def test_read_from_config_file(self):
        github_config = GitHubConfig()
        github_config.username = 'foo'
        github_config.token = 'bar'
        flags = argparse.Namespace(github_username=None, github_token=None)
        result = support.parse_github_credentials(github_config, flags)
        assert {'username': 'foo', 'token': 'bar'} == result

    def test_read_from_argv(self):
        github_config = GitHubConfig()
        flags = argparse.Namespace(github_username='spam', github_token='eggs')
        result = support.parse_github_credentials(github_config, flags)
        assert {'username': 'spam', 'token': 'eggs'} == result

    def test_read_from_config_file_and_argv(self):
        # If we get values both in the config file and in sys.argv, the latter
        # should win.
        github_config = GitHubConfig()
        github_config.username = 'foo'
        github_config.token = 'bar'
        flags = argparse.Namespace(github_username='spam', github_token='eggs')
        result = support.parse_github_credentials(github_config, flags)
        assert {'username': 'spam', 'token': 'eggs'} == result

    def test_no_credentials_error(self):
        github_config = GitHubConfig()
        flags = argparse.Namespace(github_username=None, github_token=None)
        with pytest.raises(SystemExit):
            support.parse_github_credentials(github_config, flags)


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
