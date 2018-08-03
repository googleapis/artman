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
