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
from copy import copy
import getpass
import importlib
import io
import logging
import os

import six

from ruamel import yaml

from artman.utils.logger import logger
from artman.utils.logger import setup_logging

__all__ = ('configure',)


def configure(log_level=logging.INFO):
    """Allow the user to write a new configuration file.

    Returns:
        int: An exit status.
    """
    user_config = {}

    # Walk the user through basic configuration.
    setup_logging(log_level)
    logger.info('Welcome to artman. We will get you configured.')
    logger.info('When this is done, config will be stored in ~/.artman/config.yaml.')
    logger.info('')

    # Go through each step.
    # These are split out to make testing them easier.
    user_config['local_paths'] = _configure_local_paths(
        user_config.get('local_paths', {}),
    )
    user_config['publish'] = _configure_publish()
    if user_config['publish'] == 'github':
        user_config['github'] = _configure_github(
            user_config.get('github', {}),
        )

    # Write the final configuration.
    config_yaml = yaml.dump(user_config,
        block_seq_indent=2,
        default_flow_style=False,
        indent=2,
    )
    if isinstance(config_yaml, six.binary_type):
        config_yaml = config_yaml.decode('utf8')
    try:
        os.makedirs(os.path.expanduser('~/.artman/'))
    except OSError:
        pass
    with io.open(os.path.expanduser('~/.artman/config.yaml'), 'w+') as file_:
        file_.write(u'---\n')
        file_.write(config_yaml)
    logger.success('Configuration written successfully to '
                   '~/.artman/config.yaml.')


def _configure_local_paths(local_paths):
    """Return a copy of user_config with local_paths set.

    Args:
        local_paths (dict): The starting local_paths portion ofuser config.

    Returns:
        dict: The new local_paths dictionary.
    """
    answer = copy(local_paths)

    # Ask the user for a repository root.
    while not answer.get('reporoot'):
        logger.info('First, we need to know where you store most code on your '
                    'local machine.')
        logger.info('Other paths (example: toolkit) will derive from this, '
                    'but most are individually configurable.')
        logger.info('The use of ${REPOROOT} in GAPIC YAMLs will point here.')
        logger.info('Note: Use of ~ is fine here.')
        answer['reporoot'] = six.moves.input('Local code path: ')
        answer['reporoot'] = answer['reporoot'].rstrip('/').strip()

    # Set up dependent directories.
    reporoot = answer['reporoot']
    for dep in ('api-client-staging', 'googleapis', 'toolkit'):
        location = six.moves.input(
            'Path for {0} (default: {1}/{0}): '.format(dep, reporoot)
        ).rstrip('/').strip()
        if location:
            answer[dep.replace('-', '_')] = location

    # Done; return the answer.
    return answer


def _configure_publish(publish=None):
    """Determine and return the default publisher.

    Args:
        publish (str): The current default publisher (may be None).

    Returns:
        str: The new default publisher.
    """
    # Set up publishing defaults.
    logger.info('Where do you want to publish code by default?')
    logger.info('The common valid options are "github" and "local".')
    publish = six.moves.input('Default publisher: ').lower()
    try:
        importlib.import_module('artman.tasks.publish.%s' % publish)
        return publish
    except ImportError:
        logger.error('Invalid publisher.')
        return _configure_publish()


def _configure_github(github):
    """Determine and return the GitHub configuration.

    Args:
        github (dict): The current GitHub configuration.

    Returns:
        dict: The new GitHub configuration.
    """
    answer = copy(github)
    logger.info('Since you intend to publish to GitHub, you need to '
                'supply credentials.')
    logger.info('Create an access token at: '
                'https://github.com/settings/tokens')
    logger.info('It needs the "repo" scope and nothing else.')
    while not answer.get('username'):
        answer['username'] = six.moves.input('GitHub username: ')
    while not answer.get('token'):
        answer['token'] = getpass.getpass('GitHub token (input is hidden): ')
    return answer
