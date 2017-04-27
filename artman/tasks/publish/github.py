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


class CreateGitHubBranch(task_base.TaskBase):
    """Create a new branch on GitHub with the appropriate GAPIC.

    This task requires WRITE access to the applicable repository.
    """
    default_provides = 'branch_name'

    def execute(self, git_repo, api_name, api_version, language,
                output_dir, gapic_code_dir, grpc_code_dir=None):
        """Clone a repository from GitHub into a temporary location.

        Args:
            git_repo (dict): Information about the git repository.
            api_name (str): The name of the API.
            api_version (str): The version of the API.
            language (str): The name of the language.
            output_dir (str): The name of the original output directory.
                This directory is removed entirely.
            gapic_code_dir (str): The location of the GAPIC code.
            grpc_code_dir (str): The location of the GRPC code, if any.

        Returns:
            str: The name of the branch.
        """
        # Determine where the repository should go.
        tmp = os.environ.get('ARTMAN_TEMP_DIR', '%stmp' % os.path.sep)
        repo_temp_dir = os.path.join(tmp, str(uuid.uuid4())[0:8])

        # Ensure we know where we are, so we can make this task not
        # ultimately mutate the working directory.
        original_directory = os.curdir

        # Make the GAPIC code directory an absolute path, since we will be
        # moving around.
        gapic_code_dir = os.path.realpath(gapic_code_dir)

        # Check out the code from GitHub.
        repo = git_repo['location']
        component = git_repo.get('gapic_component', '.')
        logger.info('Checking out fresh clone of %s.' % repo)
        try:
            self.exec_command(['git', 'clone', repo, repo_temp_dir])

            # Create a new branch for this API.
            branch_name = '{api_name}-{language}-{api_version}-{salt}'.format(
                api_name=api_name.lower(),
                api_version=api_version.lower(),
                language=language.lower(),
                salt=str(uuid.uuid4())[0:8],
            )
            os.chdir(repo_temp_dir)
            logger.info('Creating the {0} branch.'.format(branch_name))
            self.exec_command(['git', 'checkout', '-b', branch_name])

            # Copy the previously-generated GAPIC into the temporary
            # repository.
            gapic_subpath = git_repo.get('gapic_subpath', '.')
            src_path = os.path.abspath(os.path.join(gapic_code_dir, component))
            self.exec_command(['git', 'rm', '-r', '--force',
                               '--ignore-unmatch', gapic_subpath])
            self.exec_command(['cp', '-rf', src_path, gapic_subpath])
            self.exec_command(['git', 'add', gapic_subpath])

            # Commit the GAPIC.
            self.exec_command(['git', 'commit', '--allow-empty', '-m',
                '{language} GAPIC: {api_name} {api_version}'.format(
                    api_name=api_name,
                    api_version=api_version,
                    language=language.capitalize(),
                ),
            ])

            # If there is a separate GRPC to be staged, handle this also.
            grpc_subpath = git_repo.get('grpc_subpath', None)
            if grpc_subpath:
                self.exec_command(['git', 'rm', '-r', '--force',
                                   '--ignore-unmatch', grpc_subpath])
                self.exec_command(['cp', '-rf', grpc_code_dir, grpc_subpath])
                self.exec_command(['git', 'add', grpc_subpath])
                self.exec_command(['git', 'commit', '--allow-empty', '-m',
                    '{language} GRPC/Proto: {api_name} {api_version}'.format(
                        api_name=api_name,
                        api_version=api_version,
                        language=language.capitalize(),
                    ),
                ])

            # Push the branch to GitHub.
            self.exec_command(['git', 'push', 'origin', branch_name])
            logger.info('Code pushed to GitHub as `%s` branch.' % branch_name)

            # Remove the original output directory.
            self.exec_command(['rm', '-rf', output_dir])

            # Return the branch name. This is needed in order to create a
            # pull request from that branch.
            return branch_name
        finally:
            # Ensure we clean up after ourselves by removing the temporary
            # repository directory.
            self.exec_command(['rm', '-rf', repo_temp_dir])

            # Change the working directory back to where we started.
            os.chdir(original_directory)


class CreateGitHubPullRequest(task_base.TaskBase):
    """Create a pull request on GitHub to merge the branch.

    This task requires WRITE access to the repository.
    """
    default_provides = 'pull_request'

    def execute(self, git_repo, github, branch_name, api_name, api_version,
                language):
        """Create a pull request on GitHub.

        Args:
            api_version (str): The version of the API. Used in the title of
                the pull request.
            language (str): The name of the language. Used in the title
                of the pull request.
        """
        # Determine the pull request title.
        pr_title = '{language} GAPIC: {api_name} {api_version}'.format(
            api_name=api_name,
            api_version=api_version,
            language=language.capitalize(),
        )

        # Determine the repo owner and name from the location, which is how
        # this API expects to receive this data.
        repo_loc = git_repo['location'].rstrip('/')
        repo_owner, repo_name = repo_loc.split(':')[-1].split('/')[-2:]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        # Instantiate the repo object.
        gh = github3.login(github['username'], github['token'])
        repo = gh.repository(repo_owner, repo_name)

        # Create the pull request.
        pr = repo.create_pull(
            base=git_repo.get('branch', 'master'),
            body='This pull request was generated by artman. '
                 'Please review it thoroughly before merging.',
            head=branch_name,
            title=pr_title,
        )

        # If we did not successfully create a pull request, this is an
        # error.
        if not pr:
            logger.error('Failed to create a pull request. You will need to '
                         'create a PR manually.')
            raise RuntimeError('Pull request creation failed.')

        # Log that the PR was created.
        logger.success('Pull request created: {url}'.format(
            url=pr.html_url,
        ))

        # Return back the pull request object.
        return pr


TASKS = (
    CreateGitHubBranch,
    CreateGitHubPullRequest,
)
