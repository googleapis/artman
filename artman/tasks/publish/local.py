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

import six

from artman.tasks import task_base
from artman.utils.logger import logger


class LocalStagingTask(task_base.TaskBase):
    """Create a new branch on GitHub with the appropriate GAPIC.

    This task requires WRITE access to the applicable repository.
    """
    def execute(self, git_repo, local_paths, output_dir,
        gapic_code_dir=None, grpc_code_dir=None, proto_code_dir=None):
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

        # Track our code directories, and use absolute paths, since we will
        # be moving around.
        code_dirs = {}
        if gapic_code_dir:
            code_dirs['gapic'] = os.path.abspath(gapic_code_dir)
        if grpc_code_dir:
            code_dirs['grpc'] = os.path.abspath(grpc_code_dir)
        if proto_code_dir:
            code_dirs['proto'] = os.path.abspath(proto_code_dir)

        if not code_dirs:
            raise RuntimeError('No code path is defined.')

        # Keep track of all destinations so we are not too eager on wiping
        # out code from the original output area.
        #
        # This also allows useful output to the user in the success message.
        dests = []

        # Sanity check: The git repository must explicitly define the paths
        # where the generated code goes. If that is missing, fail now.
        if not git_repo.get('paths'):
            raise RuntimeError('This git repository entry in the artman YAML '
                               'does not define module paths.')
            
        # Determine where the code belongs and stage it there.
        for path in git_repo['paths']:
            # Piece together where we are copying code from and to.
            if isinstance(path, (six.text_type, six.binary_type)):
                path = {'dest': path}
            artifact = path.get('artifact', 'gapic')

            if artifact in code_dirs:
                # Convert everything to an absolute path.
                src = os.path.abspath(os.path.join(code_dirs[artifact], path.get('src', '.')))
                dest = os.path.abspath(os.path.join(api_repo, path.get('dest', '.')))

                # All src path does not necessarily exist. For example, gapic src directory will
                # not be created for ProtoClientPipeline
                if os.path.isdir(src):
                    # Keep track of all code destinations, for output later.
                    dests.append(dest)

                    # Actually copy the code.
                    self.exec_command(['rm', '-rf', dest])
                    self.exec_command(['cp', '-rf', src, dest])

        # Remove the original paths.
        if gapic_code_dir and os.path.isdir(gapic_code_dir):
            self.exec_command(['rm', '-rf', gapic_code_dir])
        if grpc_code_dir and os.path.isdir(grpc_code_dir):
            self.exec_command(['rm', '-rf', grpc_code_dir])
        if all([output_dir not in d for d in dests]) and os.path.isdir(output_dir):
            self.exec_command(['rm', '-rf', output_dir])

        # Log a useful success message.
        userhome = os.path.expanduser('~')
        for d in dests:
            location = d.replace(userhome, '~')
            logger.success('Code generated: {0}'.format(location))


TASKS = (
    LocalStagingTask,
)
