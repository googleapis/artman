# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Prepare a new artman release.

This script updates SHA hashes of latest commits for both gapic-generator
and googleapis, and updates version number for subsequent (auto-)release.

usage: update-versions.py [-h] [--fetch-googleapis] [--fetch-gapic-generator]
                          [version]
"""

import argparse
import os.path
import re
import requests
import sys
from ruamel.yaml import YAML

dockerfile_googleapis_regex = r'^(ENV GOOGLEAPIS_HASH )\S+()'
dockerfile_gapic_generator_regex = r'^(ENV GAPIC_GENERATOR_HASH )\S+()'
dockerfile_version_regex = r'^(ENV ARTMAN_VERSION )\S+()'
setup_py_version_regex = r"^(current_version = ')\S+(')"

github_gapic_generator_project = 'googleapis/gapic-generator'
github_googleapis_project = 'googleapis/googleapis'


def get_latest_commit_sha(project):
    url = 'https://api.github.com/repos/{}/branches/master'.format(project)
    # try to get GitHub credentials from config
    auth = None
    config = None
    artman_config = os.path.join(os.environ['HOME'], '.artman', 'config.yaml')
    try:
        yaml = YAML()
        with open(artman_config) as config_yaml:
            config = yaml.load(config_yaml)
    except:
        print('Cannot read config file {}.'.format(artman_config))
        print('Error: {}'.format(sys.exc_info()[1]))

    if config:
        try:
            github_username = config['github']['username']
            github_token = config['github']['token']
            auth = requests.auth.HTTPBasicAuth(github_username, github_token)
        except:
            print(
                'Cannot get GitHub token from {}, trying anonymously.'.format(
                    artman_config))
            print('Error: {}'.format(sys.exc_info()[1]))
            print('You can add your GitHub token to artman config.yaml:')
            print('github:')
            print('  username:')
            print('  password:')

    sha = None
    try:
        response = requests.get(url, auth=auth)
        repo = response.json()
        sha = repo['commit']['sha']
    except:
        print('Cannot get latest commit SHA.')
        print('Error: {}'.format(sys.exc_info()[1]))
        print(
            'If you connect to GitHub anonymously, try adding your token to config.yaml.'
        )

    return sha


def update_file(filename, regex, version):
    lines = []
    with open(filename) as f:
        for line in f:
            line = re.sub(regex, r'\g<1>' + version + r'\g<2>', line)
            lines.append(line)
    with open(filename, 'w') as f:
        f.write(''.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Prepare new artman release.')
    parser.add_argument(
        'version', nargs='?', help='Set version (MAJOR.MINOR.PATCH).')
    parser.add_argument(
        '--fetch-googleapis',
        action='store_true',
        help=
        'Fetch the latest googleapis commit SHA from GitHub and store in Dockerfile.'
    )
    parser.add_argument(
        '--fetch-gapic-generator',
        action='store_true',
        help=
        'Fetch the latest gapic-generator commit SHA from GitHub and store in Dockerfile.'
    )

    args = parser.parse_args()

    if not args.version and not args.fetch_googleapis and not args.fetch_gapic_generator:
        parser.print_help()
        return

    # Parameters validation

    if args.version and not re.match(r'^\d+\.\d+\.\d+(?:-\w+)?$',
                                     args.version):
        parser.print_help()
        raise ValueError('Version must be MAJOR.MINOR.PATCH.')

    # Fetch SHA if needed
    googleapis_sha = None
    if args.fetch_googleapis:
        sha = get_latest_commit_sha(github_googleapis_project)
        if not sha:
            raise RuntimeError('Cannot get googleapis commit hash.')
        googleapis_sha = sha

    gapic_generator_sha = None
    if args.fetch_gapic_generator:
        sha = get_latest_commit_sha(github_gapic_generator_project)
        if not sha:
            raise RuntimeError('Cannot get gapic-generator commit hash.')
        gapic_generator_sha = sha

    # Locate files to update
    abspath = os.path.abspath(parser.prog)
    root_dir = os.path.dirname(abspath)
    dockerfile = os.path.join(root_dir, 'Dockerfile')
    setup_py = os.path.join(root_dir, 'setup.py')

    # Do what they asked
    if googleapis_sha:
        update_file(dockerfile, dockerfile_googleapis_regex, googleapis_sha)
        print('googleapis commit SHA is now ' + googleapis_sha + '.')

    if gapic_generator_sha:
        update_file(dockerfile, dockerfile_gapic_generator_regex,
                    gapic_generator_sha)
        print('gapic_generator commit SHA is now ' + gapic_generator_sha + '.')

    if args.version:
        update_file(dockerfile, dockerfile_version_regex, args.version)
        update_file(setup_py, setup_py_version_regex, args.version)
        print('Version is now ' + args.version + '.')


if __name__ == '__main__':
    main()
