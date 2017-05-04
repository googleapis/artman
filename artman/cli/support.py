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
import sys

from ruamel import yaml

from artman.utils.logger import logger


def parse_github_credentials(config, argv_flags):
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
        'username' in config or argv_flags.github_username,
        'token' in config or argv_flags.github_token,
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
        'username': argv_flags.github_username or config['username'],
        'token': argv_flags.github_token or config['token'],
    }


def parse_local_paths(user_config, flags):
    """Parse all relevant local flags, given appropriate user config and flags.

    Args:
        user_config (dict): The user config, usually ~/.artman/config.yaml
        flags (argparse.Namespace): The flags sent to sys.argv

    Returns:
        dict: A dictionary with, at minimum, the following keys:
            reporoot, artman, api_client_staging, googleapis toolkit
    """
    local_paths = user_config.get('local_paths', {})

    # Set all defaults.
    local_paths.setdefault('reporoot', '..')
    local_paths.setdefault('artman', '{reporoot}/artman')
    local_paths.setdefault('api_client_staging',
                           '{reporoot}/api-client-staging')
    local_paths.setdefault('googleapis', '{reporoot}/googleapis')
    local_paths.setdefault('toolkit', '{reporoot}/toolkit')

    # Only googleapis can be set with flags (this allows a temporary pointer
    # to googleapis-private if the developer uses a different directory for
    # that).
    if flags.googleapis:
        local_paths['googleapis'] = flags.googleapis

    # Make all paths absolute, resolve reporoot, and expand the ~.
    for key, path in local_paths.items():
        path = path.format(reporoot=local_paths['reporoot'])
        path = os.path.realpath(os.path.expanduser(path)).rstrip('/')
        local_paths[key] = path

    # Done; return the local paths. These are used for substitution in
    # later configuration files.
    return local_paths


def resolve(name, user_config, flags, default=None):
    """Resolve the provided option from either user_config or flags.

    If neither is set, use the default.
    If both are set, the flags take precedence.
    """
    answer = user_config.get(name, default)
    if getattr(flags, name, None):
        answer = getattr(flags, name)
    return answer


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


