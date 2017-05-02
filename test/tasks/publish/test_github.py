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
from argparse import Namespace
import os
import unittest
import uuid

import github3

import mock

import pytest

from artman.tasks.publish import github
from artman.utils.logger import logger


class CreateGitHubBranchTests(unittest.TestCase):
    @mock.patch.object(github.CreateGitHubBranch, 'exec_command')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(uuid, 'uuid4')
    def test_execute(self, uuid4, chdir, exec_command):
        uuid4.return_value = uuid.UUID('00000000-0000-0000-0000-000000000000')

        # Run the task.
        task = github.CreateGitHubBranch()
        branch_name = task.execute(
            api_name='pubsub',
            api_version='v1',
            gapic_code_dir='/path/to/code',
            git_repo={
                'location': 'git@github.com:me/repo.git',
                'paths': ['generated/ruby/gapic-google-cloud-pubsub-v1'],
            },
            language='ruby',
            output_dir='/path/to',
        )

        # List the commands that should have been executed.
        expected_commands = (
            'git clone git@github.com:me/repo.git /tmp/00000000',
            'git checkout -b pubsub-ruby-v1-00000000',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/ruby/gapic-google-cloud-pubsub-v1',
            ]),
            'cp -rf /path/to/code generated/ruby/gapic-google-cloud-pubsub-v1',
            'git add generated/ruby/gapic-google-cloud-pubsub-v1',
            'git commit --allow-empty -m Ruby GAPIC: Pubsub v1', # Close enough
            'git push origin pubsub-ruby-v1-00000000',
            'rm -rf /path/to',
            'rm -rf /tmp/00000000',
        )

        # Now prove that they were.
        assert exec_command.call_count == len(expected_commands)
        for cmd, exec_call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = exec_call
            assert ' '.join(args[0]) == cmd

    @mock.patch.object(github.CreateGitHubBranch, 'exec_command')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(uuid, 'uuid4')
    def test_execute_with_non_master_base(self, uuid4, chdir, exec_command):
        uuid4.return_value = uuid.UUID('00000000-0000-0000-0000-000000000000')

        # Run the task.
        task = github.CreateGitHubBranch()
        branch_name = task.execute(
            api_name='pubsub',
            api_version='v1',
            gapic_code_dir='/path/to/code',
            git_repo={
                'location': 'git@github.com:me/repo.git',
                'branch': 'pubsub',
                'paths': ['generated/ruby/gapic-google-cloud-pubsub-v1'],
            },
            language='ruby',
            output_dir='/path/to',
        )

        # List the commands that should have been executed.
        expected_commands = (
            'git clone git@github.com:me/repo.git /tmp/00000000',
            'git checkout --track -b pubsub origin/pubsub',
            'git checkout -b pubsub-ruby-v1-00000000',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/ruby/gapic-google-cloud-pubsub-v1',
            ]),
            'cp -rf /path/to/code generated/ruby/gapic-google-cloud-pubsub-v1',
            'git add generated/ruby/gapic-google-cloud-pubsub-v1',
            'git commit --allow-empty -m Ruby GAPIC: Pubsub v1',
            'git push origin pubsub-ruby-v1-00000000',
            'rm -rf /path/to',
            'rm -rf /tmp/00000000',
        )

        # Now prove that they were.
        assert exec_command.call_count == len(expected_commands)
        for cmd, exec_call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = exec_call
            assert ' '.join(args[0]) == cmd

    @mock.patch.object(github.CreateGitHubBranch, 'exec_command')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(uuid, 'uuid4')
    def test_execute_with_grpc(self, uuid4, chdir, exec_command):
        uuid4.return_value = uuid.UUID('00000000-0000-0000-0000-000000000000')

        # Run the task.
        task = github.CreateGitHubBranch()
        branch_name = task.execute(
            api_name='pubsub',
            api_version='v1',
            gapic_code_dir='/path/to/code',
            grpc_code_dir='/path/to/grpc_code',
            git_repo={
                'location': 'git@github.com:me/repo.git',
                'paths': [
                    'generated/python/gapic-pubsub-v1',
                    {
                        'artifact': 'grpc',
                        'dest': 'generated/python/proto-pubsub-v1',
                    },
                ],
            },
            language='python',
            output_dir='/path/to',
        )

        # List the commands that should have been executed.
        expected_commands = (
            'git clone git@github.com:me/repo.git /tmp/00000000',
            'git checkout -b pubsub-python-v1-00000000',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/python/gapic-pubsub-v1',
            ]),
            'cp -rf /path/to/code generated/python/gapic-pubsub-v1',
            'git add generated/python/gapic-pubsub-v1',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/python/proto-pubsub-v1',
            ]),
            'cp -rf /path/to/grpc_code generated/python/proto-pubsub-v1',
            'git add generated/python/proto-pubsub-v1',
            'git commit --allow-empty -m Python GAPIC: Pubsub v1',
            'git push origin pubsub-python-v1-00000000',
            'rm -rf /path/to',
            'rm -rf /tmp/00000000',
        )

        # Now prove that they were.
        assert exec_command.call_count == len(expected_commands)
        for cmd, exec_call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = exec_call
            assert ' '.join(args[0]) == cmd

    @mock.patch.object(github.CreateGitHubBranch, 'exec_command')
    @mock.patch.object(os, 'chdir')
    @mock.patch.object(uuid, 'uuid4')
    def test_execute_with_grpc_explicit_src(self, uuid4, chdir, exec_command):
        uuid4.return_value = uuid.UUID('00000000-0000-0000-0000-000000000000')

        # Run the task.
        task = github.CreateGitHubBranch()
        branch_name = task.execute(
            api_name='pubsub',
            api_version='v1',
            gapic_code_dir='/path/to/code',
            grpc_code_dir='/path/to/grpc_code',
            git_repo={
                'location': 'git@github.com:me/repo.git',
                'paths': [{
                    'src': 'gapic',
                    'dest': 'generated/python/gapic-pubsub-v1',
                }, {
                    'artifact': 'grpc',
                    'src': 'proto',
                    'dest': 'generated/python/proto-pubsub-v1',
                }],
            },
            language='python',
            output_dir='/path/to',
        )

        # List the commands that should have been executed.
        expected_commands = (
            'git clone git@github.com:me/repo.git /tmp/00000000',
            'git checkout -b pubsub-python-v1-00000000',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/python/gapic-pubsub-v1',
            ]),
            'cp -rf /path/to/code/gapic generated/python/gapic-pubsub-v1',
            'git add generated/python/gapic-pubsub-v1',
            ' '.join([
                'git rm -r --force --ignore-unmatch',
                'generated/python/proto-pubsub-v1',
            ]),
            'cp -rf /path/to/grpc_code/proto generated/python/proto-pubsub-v1',
            'git add generated/python/proto-pubsub-v1',
            'git commit --allow-empty -m Python GAPIC: Pubsub v1',
            'git push origin pubsub-python-v1-00000000',
            'rm -rf /path/to',
            'rm -rf /tmp/00000000',
        )

        # Now prove that they were.
        assert exec_command.call_count == len(expected_commands)
        for cmd, exec_call in zip(expected_commands, exec_command.mock_calls):
            _, args, _ = exec_call
            assert ' '.join(args[0]) == cmd


class CreateGitHubPullRequestTests(unittest.TestCase):
    def setUp(self):
        self.task_kwargs = {
            'api_name': 'pubsub',
            'api_version': 'v1',
            'branch_name': 'pubsub-python-v1',
            'git_repo': {
                'location': 'git@github.com:me/repo.git',
            },
            'github': {
                'username': 'lukesneeringer',
                'token': '1335020400',
            },
            'language': 'python',
        }

    @mock.patch.object(github3, 'login')
    def test_with_ssh_repo(self, login):
        # Set up test data to return when we attempt to make the
        # pull request.
        gh = mock.MagicMock(spec=github3.github.GitHub)
        login.return_value = gh
        url = 'https://github.com/me/repo/pulls/1/'
        gh.repository().create_pull.return_value = Namespace(html_url=url)

        # Run the task.
        task = github.CreateGitHubPullRequest()
        pr = task.execute(**self.task_kwargs)

        # Assert we got the correct result.
        assert pr.html_url == url

        # Assert that the correct methods were called.
        login.assert_called_once_with('lukesneeringer', '1335020400')
        gh.repository.assert_called_with('me', 'repo')
        gh.repository().create_pull.assert_called_once_with(
            base='master',
            body='This pull request was generated by artman. '
                 'Please review it thoroughly before merging.',
            head='pubsub-python-v1',
            title='Python GAPIC: Pubsub v1',
        )

    @mock.patch.object(github3, 'login')
    def test_with_http_url(self, login):
        # Set up test data to return when we attempt to make the
        # pull request.
        gh = mock.MagicMock(spec=github3.github.GitHub)
        login.return_value = gh
        url = 'https://github.com/me/repo/pulls/1/'
        gh.repository().create_pull.return_value = Namespace(html_url=url)

        # Run the task.
        task = github.CreateGitHubPullRequest()
        pr = task.execute(**dict(self.task_kwargs, git_repo={
            'location': 'https://github/me/repo/',
        }))

        # Assert we got the correct result.
        assert pr.html_url == url

        # Assert that the correct repository method was still called.
        gh.repository.assert_called_with('me', 'repo')

    @mock.patch.object(github3, 'login')
    def test_pr_failure(self, login):
        # Set up test data to return when we attempt to make the
        # pull request.
        gh = mock.MagicMock(spec=github3.github.GitHub)
        login.return_value = gh
        gh.repository().create_pull.return_value = None

        # Run the task; it should raise RuntimeError.
        task = github.CreateGitHubPullRequest()
        with pytest.raises(RuntimeError):
            task.execute(**self.task_kwargs)
