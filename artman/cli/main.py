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

"""CLI to execute pipeline either locally or remotely."""

from __future__ import absolute_import
from logging import DEBUG, INFO
import argparse
import ast
import base64
import getpass
import io
import os
import sys
import tempfile
import time
import uuid

from gcloud import storage
from gcloud import logging

from ruamel import yaml

from taskflow import engines, task, states

from artman.cli.support import parse_github_credentials
from artman.cli.support import parse_local_paths
from artman.cli.support import resolve
from artman.pipelines import pipeline_factory
from artman.utils import job_util, pipeline_util, config_util
from artman.utils.logger import logger, setup_logging


def main(*args):
    # If no arguments are sent, we are using the entry point; derive
    # them from sys.argv.
    if not args:
        args = sys.argv[1:]

    # Get to a normalized set of arguments.
    flags = parse_args(*args)
    user_config = read_user_config(flags)
    pipeline_name, pipeline_kwargs, env = normalize_flags(flags, user_config)

    # Flesh out the pipline arguments with information gleamed from
    # loading the appropriate config in the googleapis local repo.
    pipeline_kwargs = _load_local_repo(
        pipeline_kwargs['local_paths']['googleapis'],
        **pipeline_kwargs
    )

    if flags.remote:
        # Execute pipeline task remotely based on the specified env param.
        pipeline = pipeline_factory.make_pipeline(
            pipeline_name, True, **pipeline_kwargs)
        jb = job_util.post_remote_pipeline_job_and_wait(pipeline, env)
        task_details, flow_detail = job_util.fetch_job_status(jb, env)

        for task_detail in task_details:
            if (task_detail.name.startswith('BlobUploadTask') and
                        task_detail.results):
                bucket_name, path, _ = task_detail.results
                pipeline_util.download_from_gcs(
                    bucket_name,
                    path,
                    os.path.join(tempfile.gettempdir(), 'artman-remote'))

        if flow_detail.state != 'SUCCESS':
            # Print the remote log if the pipeline execution completes but not
            # with SUCCESS status.
            _print_log(pipeline_kwargs['pipeline_id'])

    else:
        pipeline = pipeline_factory.make_pipeline(
            pipeline_name, False, **pipeline_kwargs)
        # Hardcoded to run pipeline in serial engine, though not necessarily.
        engine = engines.load(pipeline.flow, engine='serial',
                              store=pipeline.kwargs)
        engine.run()


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--language',
        default=None,
        help='Specify the language in which to generate output.',
    )
    api = parser.add_mutually_exclusive_group(required=True)
    api.add_argument('--api',
        default=None,
        help='The name of the API to generate. It must match a file in '
             '{googleapis}/gapic/api/artman_{api}.yml',
    )
    api.add_argument('--config',
        default='',
        type=str,
        help='Comma-delimited list of yaml config files. Each file may '
             'be followed by a colon (:) and then a |-delimited list of '
             'sections to be loaded from the config file. When this list '
             'of config sections is not provided, it will default to '
             '":common|<language>". An example with two config section is: '
             '/path/to/config.yaml:config_section_A|config_section_B. '
             'This is an advanced feature; for most cases, use `--api`.',
    )
    parser.add_argument('--publish',
        choices=('github', 'local', 'maven', 'noop'),
        default=None,
        help='Set where to publish the code. Options are "github", "local", '
             '"maven", and "noop". The default is "github". This can also be '
             'set in the user config file.',
    )
    parser.add_argument('--target',
        default=None,
        dest='target',
        help='If the "github" or "local" publisher is used, define which '
             'repository to publish to. The artman config YAML may specify '
             'a default for this, in which case this argument may be omitted.',
    )
    parser.add_argument('--pipeline',
        default='GapicClientPipeline',
        dest='pipeline_name',
        type=str,
        help='The name of the pipeline to run',
    )
    parser.add_argument('--pipeline-kwargs',
        type=str,
        default='{}',
        help='pipeline_kwargs string, e.g. '
             "{'sleep_secs':3, 'type':'sample'}",
    )
    parser.add_argument('--googleapis',
        type=str,
        default=None,
        help='Local path to the googleapis repository. Can also be set in '
             'the user config file under local_paths.googleapis. If not set, '
             'defaults to ${reporoot}/googleapis',
    )
    parser.add_argument('--remote',
        action='store_true',
        help='Triggers remote execution. Pipeline will be executed locally if '
             'this flag is not provided.',
    )
    parser.add_argument('--github-username',
        default=None,
        help='The GitHub username. Must be set if publishing, but can come '
             'from the user config file.',
    )
    parser.add_argument('--github-token',
        default=None,
        help='The GitHub token (or password, but do not do that). Must be set '
             'if publishing, but can come from the user config file.',
    )
    verbosity = parser.add_mutually_exclusive_group(required=False)
    verbosity.add_argument('-v', '--verbose',
        action='store_const',
        const=10,
        default=None,
        dest='verbosity',
        help='Show verbose / debug output.',
    )
    verbosity.add_argument('-q', '--quiet',
        action='store_const',
        const=25,
        default=None,
        dest='verbosity',
        help='Suppress most output.',
    )
    parser.add_argument('--user-config',
        default='~/.artman/config.yaml',
        help='User configuration file for artman. Stores GitHub credentials.',
    )
    return parser.parse_args(args=args)


def read_user_config(flags):
    """Read the user config from disk and return it.

    Args:
        flags (argparse.Namespace): The flags from sys.argv.

    Returns:
        dict: The user config.
    """
    # Load the user configuration if it exists and save a dictionary.
    user_config = {}
    user_config_file = os.path.realpath(os.path.expanduser(flags.user_config))
    if os.path.isfile(user_config_file):
        with io.open(user_config_file) as ucf:
            user_config = yaml.load(ucf.read(), Loader=yaml.Loader) or {}

    # Sanity check: Is there a configuration? If not, abort.
    if not user_config:
        setup_logging(INFO)
        logger.critical('No user configuration found.')
        logger.warn('This is probably your first time running Artman.')
        logger.warn('Run `configure-artman` to get yourself set up.')
        sys.exit(64)

    # Done; return the user config.
    return user_config

def normalize_flags(flags, user_config):
    """Combine the argparse flags and user configuration together.

    Args:
        flags (argparse.Namespace): The flags parsed from sys.argv
        user_config (dict): The user configuration taken from ~/.artman/config.yaml.

    Returns:
        tuple (str, dict, str): 3-tuple containing:
            - pipeline name
            - pipeline arguments
            - 'remote' or None
    """
    pipeline_args = {}

    # Determine logging verbosity and then set up logging.
    verbosity = resolve('verbosity', user_config, flags, default=INFO)
    setup_logging(verbosity)

    # Save local paths, if applicable.
    # This allows the user to override the path to api-client-staging or
    # toolkit on his or her machine.
    pipeline_args['local_paths'] = parse_local_paths(user_config, flags)

    # Determine where to publish.
    pipeline_args['publish'] = resolve('publish', user_config, flags,
        default='github',
    )

    # Parse out the GitHub credentials iff we are publishing to GitHub.
    if pipeline_args['publish'] == 'github':
        pipeline_args['github'] = parse_github_credentials(
            argv_flags=flags,
            config=user_config.get('github', {}),
        )

    # In most cases, we get a language.
    if flags.language:
        pipeline_args['language'] = flags.language
    elif flags.pipeline_name != 'GapicConfigPipeline':
        logger.critical('--language is required for every pipeline except '
                        'GapicConfigPipeline.')
        sys.exit(64)

    # If this is remote execution, configure that.
    if flags.remote:
        pipeline_id = str(uuid.uuid4())
        # Use a unique random temp directory for remote execution.
        # TODO(ethanbao): Let remote artman decide the temp directory.
        pipeline_args['local_paths']['reporoot'] = '/tmp/artman/{id}'.format(
            id=pipeline_id,
        )
        pipeline_args['pipeline_id'] = pipeline_id

    # If we were given just an API, then expand it into the --config
    # syntax.
    if flags.api:
        googleapis = os.path.realpath(os.path.expanduser(
            pipeline_args['local_paths']['googleapis'],
        ))
        flags.config = ','.join([
            '{googleapis}/gapic/api/artman_{api}.yaml',
            '{googleapis}/gapic/lang/common.yaml',
        ]).format(
            api=flags.api,
            googleapis=googleapis,
        )

    # Parse out the full configuration.
    config_sections = ['common']
    for config_spec in flags.config.split(','):
        config_args = config_util.load_config_spec(
            config_spec=config_spec,
            config_sections=config_sections,
            repl_vars={k.upper(): v for k, v in
                       pipeline_args['local_paths'].items()},
            language=flags.language,
        )
        pipeline_args.update(config_args)

    # Add any arbitrary keyword arguments.
    if flags.pipeline_kwargs != '{}':
        logger.warn('The use of --pipeline-kwargs is discouraged.')
        cmd_args = ast.literal_eval(flags.pipeline_kwargs)
        pipeline_args.update(cmd_args)

    # Coerce `git_repos` and `target_repo` into a single git_repo.
    if pipeline_args['publish'] in ('github', 'local'):
        # Temporarily give our users a nice error if they have an older
        # googleapis checkout.
        # DEPRECATED: 2017-04-20
        # REMOVE: 2017-05-20
        if 'git_repo' in pipeline_args:
            logger.error('Your git repos are configured in your artman YAML '
                         'using a older format. Please git pull.')
            sys.exit(96)

        # Pop the git repos off of the pipeline args and select the
        # correct one.
        repos = pipeline_args.pop('git_repos')
        pipeline_args['git_repo'] = select_git_repo(repos, flags.target)

    # Print out the final arguments to stdout, to help the user with
    # possible debugging.
    pipeline_args_repr = yaml.dump(pipeline_args,
        block_seq_indent=2,
        default_flow_style=False,
        indent=2,
    )
    logger.info('Final args:')
    for line in pipeline_args_repr.split('\n'):
        if 'token' in line:
            index = line.index(':')
            line = line[:index + 2] + '<< REDACTED >>'
        logger.info('  {0}'.format(line))

    # Return the final arguments.
    # This includes a pipeline to run, arguments, and whether to run remotely.
    return (
        flags.pipeline_name,
        pipeline_args,
        'remote' if flags.remote else None,
    )


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


def _load_local_repo(private_repo_root, **pipeline_kwargs):
    files_dict = {}
    for root, dirs, files in os.walk(private_repo_root):
        for fname in files:
            path = os.path.join(root, fname)
            rel_path = os.path.relpath(path, private_repo_root)

            # Always use forward slashes, even on Windows, since remote
            # Artman will be running in GKE.
            normalized_path = '/'.join(os.path.split(rel_path))

            # Save the contents of every applicable file into a dictionary.
            with io.open(path, 'rb') as f:
                files_dict[normalized_path] = base64.b64encode(f.read())

    pipeline_kwargs['files_dict'] = files_dict
    return pipeline_kwargs


def _print_log(pipeline_id):
    # Fetch the cloud logging entry if the exection fails. Wait for 30 secs,
    # because it takes a while for the logging to become available.
    logger.critical(
        'The remote pipeline execution failed. It will wait for 30 '
        'seconds before fetching the log for remote pipeline execution.',
    )
    time.sleep(30)
    client = logging.Client()
    pipeline_logger = client.logger(pipeline_id)
    entries, token = pipeline_logger.list_entries()
    for entry in entries:
        logger.error(entry.payload)

    logger.info(
        'You can always run the following command to fetch the log entry:\n'
        '    gcloud beta logging read "logName=projects/vkit-pipeline/logs/%s"'
        % pipeline_id,
    )
