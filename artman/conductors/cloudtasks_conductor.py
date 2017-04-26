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

'''Artman conductor to claim and execute remote tasks.'''

from __future__ import absolute_import
import base64
import io
import os
import subprocess
import time
import uuid

from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build_from_document

from artman.cli import main
from artman.utils.logger import logger, output_logger


def run(queue_name):
    task_client = _create_tasks_client()
    if True:  # TODO change to when
        pull_task_response = _pull_task(task_client, queue_name)
        tasks = pull_task_response.get('tasks', [])
        if not tasks:
            # Sleep for 30 seconds if there is no tasks returned.
            logger.debug('There is no pending task. Sleep for 30 seconds.')
            time.sleep(30)
        for task in tasks:
            tmp_reporoot, artman_user_config = _prepare_dir()
            try:
                logger.info('Starting to execute task %s' % task)
                _execute_task(artman_user_config, task)
                _ack_task(task_client, task)
                logger.info('Task execution finished for %s' % task)
            except:
                logger.error('Task execution failed for %s' % task)
                _cancel_task_lease(task_client, task)
            finally:
                logger.info('Cleanup tmp directory %s' % tmp_reporoot)
                _cleanup_tmp_dir(tmp_reporoot)


def _create_tasks_client():
    credentials = GoogleCredentials.get_application_default()
    with open(
        os.path.join(os.path.dirname(__file__), 'cloudtasks.json'), 'r') as f:
            return build_from_document(f.read(), credentials=credentials)


def _pull_task(task_client, queue_name):
    body = {
      "maxTasks": 1,
      "leaseDuration": {"seconds": 300, "nanos": 0},  # Expire after 300 secs.
      "responseView": "FULL",
      "name": "%s" % queue_name
    }
    tasks = task_client.projects().locations().queues().tasks().pull(
        name=queue_name, body=body).execute()
    logger.info('Pulling tasks request returned %s' % tasks)
    return tasks


def _ack_task(task_client, task):
    body = {'scheduleTime': task['scheduleTime']}
    response = task_client.projects().locations().queues().tasks().acknowledge(
        name=task['name'],
        body=body).execute()
    logger.info('Acknowledge task request returned %s' % response)
    return response


def _cancel_task_lease(task_client, task):
    body = {'scheduleTime': task['scheduleTime'], "responseView": "FULL"}
    response = task_client.projects().locations().queues().tasks().cancelLease(
        name=task['name'],
        body=body).execute()
    logger.info('Cancel task request returned %s' % response)
    return response


def _execute_task(artman_user_config, task):
    """Execute the remote artman tasks.

    It execute the artman command with a customized artman user config and
    additional pipeline arguments."""
    task_payload = base64.b64decode(task['pullTaskTarget']['payload'])
    artman_args = task_payload.decode("utf-8").split(' ')
    artman_args.append('--user-config')
    artman_args.append(artman_user_config)
    main.main(*artman_args)


def _prepare_dir(source_repo="https://github.com/googleapis/googleapis.git"):
    """Prepare the temporary folder to task execution.

    It downloads the googleapis repo and adds a one-time artman config yaml.
    TODO(ethanbao): support loading more input files from heterogeneous data
    sources"""

    repo_root = '/tmp/artman/%s' % str(uuid.uuid4())
    logger.info('Prepare a temporary root repo: %s' % repo_root)
    try:
        os.makedirs(repo_root)
    except OSError as e:
        raise e
    logger.info('Checking out fresh clone of %s.' % source_repo)
    googleapis_dir = os.path.join(repo_root, "googleapis")
    git_clone_args = ['git', 'clone', source_repo, googleapis_dir]
    output = subprocess.check_output(git_clone_args)
    if output:
        output = output.decode('utf8')
        output_logger.success(output)

    artman_user_config = os.path.join(repo_root, 'artman-config.yaml')
    with io.open(artman_user_config, 'w+') as file_:
        file_.write(u'---\n')
        file_.write(u'local_paths:\n')
        file_.write(u'  reporoot: %s\n' % repo_root)
        if os.environ.get('TOOLKIT_HOME'):
            toolkit_home = os.environ.get('TOOLKIT_HOME')
            file_.write(u'  toolkit: %s \n' % toolkit_home)
        file_.write(u'publish: noop \n')
    return repo_root, artman_user_config


def _cleanup_tmp_dir(tmp_dir):
    subprocess.check_call(['rm', '-rf', tmp_dir])
