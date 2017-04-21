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

from __future__ import absolute_import, unicode_literals
import functools
import os
import uuid

import github3

from artman.tasks import task_base
from artman.utils.logger import logger


class LocalStagingTask(task_base.TaskBase):
    """Create a new branch on GitHub with the appropriate GAPIC.

    This task requires WRITE access to the applicable repository.
    """
    def execute(self, gapic_code_dir, git_repo, local_paths,
                output_dir, grpc_code_dir=None):
        """Copy the code to the correct local staging location.

        Args:
            gapic_code_dir (str): The location of the GAPIC code.
            git_repo (dict): Information about the git repository.
            local_paths (dict): Configured local paths; here we use it for
                knowing where api_client_staging is.
            output_dir (str): The original base output dir. This directory
                is removed after proper local code staging unless removing
                it would remove the final destination directories.
            grpc_code_dir (str): The location of the GRPC code, if any.
        """
        # Determine the actual repository name.
        # We can use this to derive the probable OS system path, as well
        # as the key we expect in `local_paths` for an override.
        repo_name = git_repo['location'].rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        # Where is the target git repo located?
        # Start by checking for an explicit path in `local_paths`, and then
        # if none is found, derive it from reporoot.
        repo_name_underscore = repo_name.replace('-', '_')
        api_repo = local_paths.get(repo_name_underscore,
            os.path.join(local_paths.get('reporoot', '..'), repo_name),
        )
        api_repo = os.path.realpath(os.path.expanduser(api_repo))

        # Make the GAPIC code directory an absolute path, since we will be
        # moving around.
        gapic_code_dir = os.path.realpath(gapic_code_dir)

        # Determine where the code belongs and stage it there.
        repo_dest = '%s/%s' % (api_repo, git_repo.get('gapic_subpath', '.'))
        component = git_repo.get('gapic_component', '.')
        src_path = os.path.abspath(os.path.join(gapic_code_dir, component))
        self.exec_command(['rm', '-rf', repo_dest])
        self.exec_command(['cp', '-rf', src_path, repo_dest])

        # Special case: If a grpc_subpath is given, copy that code.
        grpc_dest = ''
        if git_repo.get('grpc_subpath', None) and grpc_code_dir:
            grpc_dest = '%s/%s' % (api_repo, git_repo['grpc_subpath'])
            self.exec_command(['rm', '-rf', grpc_dest])
            self.exec_command(['cp', '-rf', grpc_code_dir, grpc_dest])

        # Remove the original paths.
        self.exec_command(['rm', '-rf', gapic_code_dir])
        if grpc_code_dir:
            self.exec_command(['rm', '-rf', grpc_code_dir])
        if output_dir not in repo_dest and output_dir not in grpc_dest:
            self.exec_command(['rm', '-rf', output_dir])

        # Log a useful success message.
        userhome = os.path.expanduser('~')
        if grpc_dest:
            grpc_location = grpc_dest.replace(userhome, '~')
            logger.success('Code generated: {0}'.format(grpc_location))
        location = repo_dest.replace(userhome, '~')
        logger.success('Code generated: {0}'.format(location))


TASKS = (
    LocalStagingTask,
)
