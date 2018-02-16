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

from __future__ import absolute_import, unicode_literals
import os
import subprocess
import sys

from artman.utils.logger import logger


def parse_github_credentials(github_config, argv_flags):
    """Determine the appropriate GitHub credentials.

    If there are no vaild credentials, error out with a useful message
    so that the user can get credentials.

    Args:
        config (dict): The user github configuration pulled from the user's
            configuration file (if any).
        argv_flags (argparse.Namespace): The flags pulled from the command
            line.

    Returns:
        dict: A dictionary with 'github_username' and 'github_token' keys.
    """
    # Determine whether we have valid credentials.
    valid = all([
        github_config.username or argv_flags.github_username,
        github_config.token or argv_flags.github_token,
    ])

    # No valid credentials, give a helpful error.
    if not valid:
        logger.critical('No GitHub credentials found.')
        logger.error('Valid GitHub credentials are required if you are '
                     'publishing to GitHub (--publish github).')
        logger.warn('')
        logger.warn('In order to generate the appropriate token, perform '
                    'the following steps:')
        logger.warn('  1. Open https://github.com/settings/tokens')
        logger.warn('  2. Make a new access token with the "repo" scope.')
        logger.warn('  3. Add this structure to ~/.artman/config.yaml: ')
        logger.warn('')
        logger.warn('      github:')
        logger.warn('        username: {username}')
        logger.warn('        token: {token}')
        logger.warn('')
        logger.error('This is a terminal error. Exiting.')
        sys.exit(64)

    # Return the appropriate credentials.
    return {
        'username': argv_flags.github_username or github_config.username,
        'token': argv_flags.github_token or github_config.token,
    }


def select_git_repo(git_repos, target_repo):
    """Select the appropriate Git repo based on YAML config and CLI arguments.

    Args:
        git_repos (dict): Information about git repositories.
        target_repo (str): The user-selected target repository. May be None.

    Returns:
        dict: The selected GitHub repo.
    """
    # If there is a specified target_repo, this task is trivial; just grab
    # that git repo. Otherwise, find the default.
    if target_repo:
        git_repo = git_repos.get(target_repo)
        if not git_repo:
            logger.critical('The requested target repo is not defined '
                            'for that API and language.')
            sys.exit(32)
        return git_repo

    # Okay, none is specified. Check for a default, and use "staging" if no
    # default is defined.
    for repo in git_repos.values():
        if repo.get('default', False):
            return repo
    return git_repos['staging']


def check_docker_requirements(docker_image):
    """Checks whether all docker-related components have been installed."""

    try:
        subprocess.check_output(['docker', '--version'])
    except OSError:
        logger.error(
            'Docker not found on path or is not installed. Refer to '
            'https://docs.docker.com/engine/installation about how to install '
            'Docker on your local machine.')
        sys.exit(128)

    try:
        output = subprocess.check_output(
            ['docker', 'images', '-q', docker_image])
        if not output:
            logger.error(
                'Cannot find artman Docker image. Run `docker pull %s` to '
                'pull the image.' % docker_image)
            sys.exit(128)
    except OSError:
        logger.error('Docker image check failed. Please file an issue at '
                    'https://github.com/googleapis/artman/issues.')
        sys.exit(128)
