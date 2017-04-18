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
"""Utils related to pipeline"""

import os
import subprocess

from six.moves import urllib

from taskflow import engines
from taskflow.patterns import linear_flow

from artman.tasks import io_tasks
from artman.utils.logger import logger


def validate_exists(required, **kwargs):
    for arg in required:
        if arg not in kwargs:
            raise ValueError('{0} must be provided'.format(arg))


def validate_does_not_exist(unsupported, **kwargs):
    for arg in unsupported:
        if arg in kwargs:
            raise ValueError('{0} is not supported'.format(arg))


def download(url, directory):
    filename = os.path.basename(urllib.parse.urlsplit(url).path)
    if not os.path.isfile(os.path.join(directory, filename)):
        subprocess.check_call(['mkdir', '-p', directory])
        logger.info('Downloading file from URL: %s' % url)
        subprocess.check_call(['curl', '-o', directory + filename, '-sL', url])
    return directory + filename


def task_transition(state, details):
    logger.info('Task "%s" transition to state %s.' %
                (details['task_name'], state))


def download_from_gcs(bucket_name, path, output_dir):
    flow = linear_flow.Flow('download_from_gcs')
    args = {'bucket_name': bucket_name, 'path': path, 'output_dir': output_dir}
    flow.add(io_tasks.BlobDownloadTask('BlobDownload'))
    engine = engines.load(flow, engine="serial", store=args)
    engine.run()
