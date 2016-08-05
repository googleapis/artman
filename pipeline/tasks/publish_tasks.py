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

"""Tasks for publishing artman output"""

from pipeline.tasks import task_base
from pipeline.utils import github_utils


class PypiUploadTask(task_base.TaskBase):
    """Publishes a PyPI package"""

    def execute(self, repo_url, username, password, publish_env,
                final_repo_dir):
        publish_url = repo_url + username + '/' + publish_env
        self.exec_command(
            ['devpi',
             'login',
             '--password',
             password,
             username])
        self.exec_command(['devpi', 'use', publish_url])
        self.exec_command(
            ['devpi',
             'upload',
             '--no-vcs',
             '--from-dir',
             final_repo_dir])

    def validate(self):
        return []


class MavenDeployTask(task_base.TaskBase):
    """Publishes to a Maven repository"""

    def execute(self, repo_url, username, password, publish_env,
                final_repo_dir):
        self.exec_command(
            [final_repo_dir + '/gradlew',
             'uploadArchives',
             '-PmavenRepoUrl=' + repo_url,
             '-PmavenUsername=' + username,
             '-PmavenPassword=' + password,
             '-p' + final_repo_dir])

    def validate(self):
        return []


class GitHubPushTask(task_base.TaskBase):
    """Uploads local files to GitHub repository in a new commit.

    Won't delete files (if missing in local repo) from the remote repo. If the
    remote copy of a file differs from local copy, overwrites with local copy.
    Does not change files or folders that are in remote repo but not in local
    repo.
    """
    def execute(self, owner, branch, username, password, publish_env,
                dir_to_push, message):
        github_utils.push_dir_to_github(dir_to_push, username, password, owner,
                                        publish_env, branch, message)

    def validate(self):
        return []
