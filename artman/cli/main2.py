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
"""The new artman CLI with the following syntax.

    artman [Options] generate|publish <artifact_name>

.. note::
    Only local execution is supported at this moment. The CLI syntax is
    beta, and might have changes in the future.
"""

from __future__ import absolute_import
from logging import DEBUG, INFO
import argparse
from distutils.dir_util import copy_tree
import io
import os
import pprint
import subprocess
import sys

from ruamel import yaml

from taskflow import engines

from artman.config import converter, loader
from artman.config.proto.config_pb2 import Artifact, Config
from artman.cli import support
from artman.pipelines import pipeline_factory
from artman.utils import config_util
from artman.utils.logger import logger, setup_logging

ARTMAN_DOCKER_IMAGE = 'googleapis/artman:0.4.17'
RUNNING_IN_ARTMAN_DOCKER_TOKEN = 'RUNNING_IN_ARTMAN_DOCKER'

def main(*args):
    """Main method of artman."""
    # If no arguments are sent, we are using the entry point; derive
    # them from sys.argv.
    if not args:
        args = sys.argv[1:]

    # Get to a normalized set of arguments.
    flags = parse_args(*args)
    user_config = read_user_config(flags)
    _adjust_input_dir(flags.input_dir)
    pipeline_name, pipeline_kwargs = normalize_flags(flags, user_config)

    if flags.local:
        pipeline = pipeline_factory.make_pipeline(pipeline_name, False,
                                                  **pipeline_kwargs)
        # Hardcoded to run pipeline in serial engine, though not necessarily.
        engine = engines.load(
            pipeline.flow, engine='serial', store=pipeline.kwargs)
        engine.run()
        _change_owner(flags, pipeline_name, pipeline_kwargs)
    else:
        support.check_docker_requirements(flags.image)
        # Note: artman currently won't work if input directory doesn't contain
        # shared configuration files (e.g. gapic/packaging/dependencies.yaml).
        # This will make artman less useful for non-Google APIs.
        # TODO(ethanbao): Fix that by checking the input directory and
        # pulling the shared configuration files if necessary.
        logger.info('Running artman command in a Docker instance.')
        _run_artman_in_docker(flags)


def _adjust_input_dir(input_dir):
    """"Adjust input directory to use versioned common config and/or protos.

    Currently che codegen has coupling with some shared configuration yaml
    under under {googleapis repo}/gapic/[core,lang,packaging], causing library
    generation to fail when a breaking change is made to such shared
    configuration file. This delivers a poor user experience to artman
    users, as their library generation could fail without any change at API
    proto side.

    Similarily, some common protos will be needed during protoc
    compilation, but is not provided by users in some cases. When such shared
    proto directories are not provided, copy and use the versioned ones.

    TODO(ethanbao): Remove the config copy once
    https://github.com/googleapis/toolkit/issues/1450 is fixed.
    """
    if os.getenv(RUNNING_IN_ARTMAN_DOCKER_TOKEN):
        # Only doing this when running inside Docker container
        common_config_dirs = [
            'gapic/core',
            'gapic/lang',
            'gapic/packaging',
        ]
        common_proto_dirs = [
            'google/api',
            'google/iam/v1',
            'google/longrunning',
            'google/rpc',
            'google/type',
        ]
        for src_dir in common_config_dirs:
            # /googleapis is the root of the versioned googleapis repo
            # inside Artman Docker image.
            copy_tree(os.path.join('/googleapis', src_dir),
                      os.path.join(input_dir, src_dir))

        for src_dir in common_proto_dirs:
            if not os.path.exists(os.path.join(input_dir, src_dir)):
                copy_tree(os.path.join('/googleapis', src_dir),
                          os.path.join(input_dir, src_dir))


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        type=str,
        default='artman.yaml',
        help='[Optional] Specify path to artman config yaml, which can be '
        'either an absolute path, or a path relative to the input '
        'directory (specified by `--input-dir` flag). Default to '
        '`artman.yaml`', )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./artman-genfiles',
        help='[Optional] Directory to store output generated by artman. '
        'Default to `./artman-genfiles`', )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='',
        help='[Optional] Directory with all input that is needed by artman, '
             'which include but not limited to API protos, service config '
             'yaml, and GAPIC config yaml. Default to the settings from user '
             'configuration.',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_const',
        const=10,
        default=None,
        dest='verbosity',
        help='Show verbose / debug output.', )
    parser.add_argument(
        '--user-config',
        default='~/.artman/config.yaml',
        help='[Optional] User configuration file to stores credentials like '
        'GitHub credentials. Default to `~/.artman/config.yaml`', )
    parser.add_argument(
        '--local',
        dest='local',
        action='store_true',
        help='[Optional] If specified, running the artman on the local host '
        'machine instead of artman docker instance that have all binaries '
        'installed. Note: one will have to make sure all binaries get '
        'installed on the local machine with this flag, a full list can '
        'be found at '
        'https://github.com/googleapis/artman/blob/master/Dockerfile', )
    parser.set_defaults(local=False)
    parser.add_argument(
        '--image',
        default=ARTMAN_DOCKER_IMAGE,
        help=('[Optional] Specify docker image used by artman when running in '
              'a Docker instance. Default to `%s`' % ARTMAN_DOCKER_IMAGE)),

    # Add sub-commands.
    subparsers = parser.add_subparsers(
        dest='subcommand', help='Support [generate|publish] sub-commands')

    # `generate` sub-command.
    parser_generate = subparsers.add_parser(
        'generate', help='Generate artifact')
    parser_generate.add_argument(
        'artifact_name',
        type=str,
        help='[Required] Name of the artifact for artman to generate. Must '
        'match an artifact in the artman config yaml.')

    # `publish` sub-command.
    parser_publish = subparsers.add_parser('publish', help='Publish artifact')
    parser_publish.add_argument(
        'artifact_name',
        type=str,
        help='[Required] Name of the artifact for artman to generate. Must '
        'match an artifact in the artman config yaml.')
    parser_publish.add_argument(
        '--target',
        type=str,
        default=None,
        required=True,
        help='[Required] Specify where the generated artifact should be '
        'published to. It is defined as publishing targets in artman '
        'config at artifact level.', )
    parser_publish.add_argument(
        '--github-username',
        default=None,
        help='[Optional] The GitHub username. Must be set if publishing the '
        'artifact to github, but can come from the user config file.', )
    parser_publish.add_argument(
        '--github-token',
        default=None,
        help='[Optional] The GitHub personal access token. Must be set if '
        'publishing the artifact to github, but can come from the user '
        'config file.', )
    parser_publish.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        help='[Optional] When specified, artman will skip the remote '
        'publishing step.', )
    parser_publish.set_defaults(dry_run=False)

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
        user_config (dict): The user configuration taken from
                            ~/.artman/config.yaml.

    Returns:
        tuple (str, dict): 2-tuple containing:
            - pipeline name
            - pipeline arguments
    """
    if flags.input_dir:
        flags.input_dir = os.path.abspath(flags.input_dir)
    flags.output_dir = os.path.abspath(flags.output_dir)
    flags.config = os.path.abspath(flags.config)
    pipeline_args = {}

    # Determine logging verbosity and then set up logging.
    verbosity = support.resolve('verbosity', user_config, flags, default=INFO)
    setup_logging(verbosity)

    # Save local paths, if applicable.
    # This allows the user to override the path to api-client-staging or
    # toolkit on his or her machine.
    pipeline_args['local_paths'] = support.parse_local_paths(
        user_config, flags.input_dir)

    # Save the input directory back to flags if it was not explicitly set.
    if not flags.input_dir:
        flags.input_dir = pipeline_args['local_paths']['googleapis']

    artman_config_path = flags.config
    if not os.path.isfile(artman_config_path):
        logger.error(
            'Artman config file `%s` doesn\'t exist.' % artman_config_path)
        sys.exit(96)

    try:
        artifact_config = loader.load_artifact_config(
            artman_config_path, flags.artifact_name, flags.input_dir)
    except ValueError as ve:
        logger.error('Artifact config loading failed with `%s`' % ve)
        sys.exit(96)

    # If we were given just an API or BATCH, then expand it into the --config
    # syntax.
    shared_config_name = 'common.yaml'
    if artifact_config.language in (Artifact.RUBY, Artifact.NODEJS,):
        shared_config_name = 'doc.yaml'

    legacy_config_dict = converter.convert_to_legacy_config_dict(
        artifact_config, flags.input_dir, flags.output_dir)
    logger.debug('Below is the legacy config after conversion:\n%s' %
                 pprint.pformat(legacy_config_dict))
    tmp_legacy_config_yaml = '%s.tmp' % artman_config_path
    with io.open(tmp_legacy_config_yaml, 'w') as outfile:
        yaml.dump(legacy_config_dict, outfile, default_flow_style=False)

    googleapis = os.path.realpath(
        os.path.expanduser(
            pipeline_args['local_paths']['googleapis'], ))
    config = ','.join([
        '{artman_config_path}',
        '{googleapis}/gapic/lang/{shared_config_name}',
    ]).format(
        artman_config_path=tmp_legacy_config_yaml,
        googleapis=googleapis,
        shared_config_name=shared_config_name,
    )

    language = Artifact.Language.Name(
        artifact_config.language).lower()

    # Set the pipeline as well as package_type and packaging
    artifact_type = artifact_config.type
    if artifact_type in (Artifact.GAPIC, Artifact.GAPIC_ONLY):
        pipeline_name = 'GapicClientPipeline'
        pipeline_args['language'] = language
    elif artifact_type in (Artifact.GRPC, Artifact.GRPC_COMMON):
        pipeline_name = 'GrpcClientPipeline'
        pipeline_args['language'] = language
    elif artifact_type == Artifact.GAPIC_CONFIG:
        pipeline_name = 'GapicConfigPipeline'
    else:
        raise ValueError('Unrecognized artifact.')

    # Parse out the full configuration.
    # Note: the var replacement is still needed because they are still being
    # used in some shared/common config yamls.
    config_sections = ['common']
    for config_spec in config.split(','):
        config_args = config_util.load_config_spec(
            config_spec=config_spec,
            config_sections=config_sections,
            repl_vars={
                k.upper(): v
                for k, v in pipeline_args['local_paths'].items()
            },
            language=language, )
        pipeline_args.update(config_args)

    # Setup publishing related config if needed.
    if flags.subcommand == 'generate':
        pipeline_args['publish'] = 'noop'
    elif flags.subcommand == 'publish':
        publishing_config = _get_publishing_config(artifact_config,
                                                   flags.target)
        if publishing_config.type == Artifact.PublishTarget.GITHUB:
            pipeline_args['publish'] = 'local' if flags.dry_run else 'github'
            pipeline_args['github'] = support.parse_github_credentials(
                argv_flags=flags,
                config=user_config.get('github', {}), )
            repos = pipeline_args.pop('git_repos')
            pipeline_args['git_repo'] = support.select_git_repo(
                repos, publishing_config.name)
        else:
            logger.error(
                'Publishing type `%s` is not supported yet.' %
                Artifact.PublishTarget.Type.Name(publishing_config.type))
            sys.exit(96)

    # Print out the final arguments to stdout, to help the user with
    # possible debugging.
    pipeline_args_repr = yaml.dump(
        pipeline_args,
        block_seq_indent=2,
        default_flow_style=False,
        indent=2, )
    logger.info('Final args:')
    for line in pipeline_args_repr.split('\n'):
        if 'token' in line:
            index = line.index(':')
            line = line[:index + 2] + '<< REDACTED >>'
        logger.info('  {0}'.format(line))

    # Clean up the tmp legacy artman config.
    os.remove(tmp_legacy_config_yaml)

    # Return the final arguments.
    return pipeline_name, pipeline_args


def _get_publishing_config(artifact_config_pb, publish_target):
    valid_options = []
    for target in artifact_config_pb.publish_targets:
        valid_options.append(target.name)
        if target.name == publish_target:
            return target
    logger.error('No publish target with `%s` configured in artifact `%s`. '
                 'Valid options are %s' %
                 (publish_target, artifact_config_pb.name, valid_options))
    sys.exit(96)


def _run_artman_in_docker(flags):
    """Executes artman command.

    Args:
        input_dir: The input directory that will be mounted to artman docker
            container as local googleapis directory.
    Returns:
        The output directory with artman-generated files.
    """
    ARTMAN_CONTAINER_NAME = 'artman-docker'
    input_dir = flags.input_dir
    output_dir = flags.output_dir
    artman_config_dirname = os.path.dirname(flags.config)
    user_config = os.path.join(os.path.expanduser('~'), '.artman')
    docker_image = flags.image

    inner_artman_cmd_str = ' '.join(sys.argv[1:])

    # TODO(ethanbao): Such folder to folder mounting won't work on windows.
    base_cmd = [
        'docker', 'run', '--name', ARTMAN_CONTAINER_NAME, '--rm', '-i', '-t',
        '-e', 'HOST_USER_ID=%s' % os.getuid(),
        '-e', 'HOST_GROUP_ID=%s' % os.getgid(),
        '-e', '%s=True' % RUNNING_IN_ARTMAN_DOCKER_TOKEN,
        '-v', '%s:%s' % (input_dir, input_dir),
        '-v', '%s:%s' % (output_dir, output_dir),
        '-v', '%s:%s' % (artman_config_dirname, artman_config_dirname),
        '-v', '%s:/home/.artman' % user_config,
        '-w', input_dir,
        docker_image, '/bin/bash', '-c'
    ]

    debug_cmd = list(base_cmd)
    debug_cmd.append('"artman2 %s; bash"' % inner_artman_cmd_str)

    cmd = base_cmd
    cmd.append('artman2 --local %s' % (inner_artman_cmd_str))
    try:
        output = subprocess.check_output(cmd)
        logger.info(output.decode('utf8'))
        return output_dir
    except subprocess.CalledProcessError as e:
        logger.error(e.output.decode('utf8'))
        logger.error(
            'Artman execution failed. For additional logging, re-run the '
            'command with the "--verbose" flag')
        raise
    finally:
        logger.debug('For further inspection inside docker container, run `%s`'
                     % ' '.join(debug_cmd))


def _change_owner(flags, pipeline_name, pipeline_kwargs):
    """Change file/folder ownership if necessary."""
    user_host_id = int(os.getenv('HOST_USER_ID', 0))
    group_host_id = int(os.getenv('HOST_GROUP_ID', 0))
    # When artman runs in Docker instance, all output files are by default
    # owned by `root`, making it non-editable by Docker host user. When host
    # user id and group id get passed through environment variables via
    # Docker `-e` flag, artman will change the owner based on the specified
    # user id and group id.
    if user_host_id and group_host_id:
        # Change ownership of output directory.
        for root, dirs, files in os.walk(flags.output_dir):
            os.chown(root, user_host_id, group_host_id)
            for d in dirs:
                os.chown(
                    os.path.join(root, d), user_host_id, group_host_id)
            for f in files:
                os.chown(
                    os.path.join(root, f), user_host_id, group_host_id)
        if 'GapicConfigPipeline' == pipeline_name:
            # There is a trick that the gapic config output is generated to
            # input directory, where it is supposed to be in order to be
            # used as an input for other artifact generation. With that
            # the gapic config output is not located in the output folder,
            # but the input folder. Make the explicit chown in this case.
            os.chown(
                pipeline_kwargs['gapic_api_yaml'][0],
                user_host_id,
                group_host_id)


if __name__ == "__main__":
    main()
