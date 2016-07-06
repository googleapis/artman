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

import subprocess
from pipeline.tasks import task_base


class PypiUploadTask(task_base.TaskBase):
    """Publishes a PyPI package"""

    def execute(self, repo_url, username, password, publish_env,
                final_repo_dir):
        publish_url = repo_url + username + '/' + publish_env
        subprocess.check_call(
            ['devpi',
             'login',
             '--password',
             password,
             username])
        subprocess.check_call(['devpi', 'use', publish_url])
        subprocess.check_call(
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
        subprocess.check_call(
            [final_repo_dir + '/gradlew',
             'uploadArchives',
             '-PmavenRepoUrl=' + repo_url,
             '-PmavenUsername=' + username,
             '-PmavenPassword=' + password,
             '-p' + final_repo_dir])

    def validate(self):
        return []
