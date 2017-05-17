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
import logging
import os
import subprocess
import sys
import time
import traceback
import uuid

from oauth2client.client import GoogleCredentials
from gcloud import logging as cloud_logging
from googleapiclient.discovery import build_from_document

from artman.cli import main
from artman.utils.logger import logger, output_logger


MAX_ATTEMPTS = 3
CLOUD_LOGGING_CLIENT = None


def run(queue_name):
    task_client = _create_tasks_client()
    while True:
        _pull_and_execute_tasks(task_client, queue_name)


def _pull_and_execute_tasks(task_client, queue_name):
    pull_task_response = _pull_task(task_client, queue_name)
    tasks = pull_task_response.get('tasks', [])
    if not tasks:
        # Sleep for 30 seconds if there is no tasks returned.
        logger.debug('There is no pending task. Sleep for 10 seconds.')
        time.sleep(10)
    for task in tasks:
        task_id, tmp_root, artman_user_config, log_file_path = _prepare_dir()
        log_file_handler = None
        try:
            log_file_handler = _setup_logger(log_file_path)
            logger.info('Starting to execute task %s' % task)
            if int(task['taskStatus']['attemptDispatchCount']) > MAX_ATTEMPTS:
                logger.info('Delete task which exceeds max attempts.')
                _delete_task(task_client, task)
                continue
            _execute_task(artman_user_config, task)
            _ack_task(task_client, task)
            logger.info('Task execution finished')
        except Exception as e:
            logger.error('\n'.join(traceback.format_tb(sys.exc_info()[2])))
            _cancel_task_lease(task_client, task)
        finally:
            logger.info('Cleanup tmp directory %s' % tmp_root)
            # Use task id as log name
            _write_to_cloud_logging(task_id, log_file_path)
            _cleanup(tmp_root, log_file_handler)


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
    body = {'scheduleTime': task['scheduleTime'], 'responseView': 'FULL'}
    response = task_client.projects().locations().queues().tasks().cancelLease(
        name=task['name'],
        body=body).execute()
    logger.info('Cancel task request returned %s' % response)
    return response


def _delete_task(task_client, task):
    response = task_client.projects().locations().queues().tasks().delete(
        name=task['name']).execute()
    logger.info('Delete task request returned %s' % response)
    return response


def _setup_logger(log_path):
    """Setup logger with one-time logging FileHandler."""
    logger = logging.getLogger('artman')
    log_file_handler = logging.FileHandler(log_path)
    logger.addHandler(log_file_handler)
    return log_file_handler


def _write_to_cloud_logging(log_id, log_file_path):
    """Write log file content to cloud logging"""
    if not CLOUD_LOGGING_CLIENT:
        CLOUD_LOGGING_CLIENT = cloud_logging.Client()
    cloud_logger = CLOUD_LOGGING_CLIENT.logger(log_id)
    if log_file_path:
        with open(log_file_path, 'r') as log_file:
            cloud_logger.log_text(log_file.read())


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

    task_id = str(uuid.uuid4())[0:8]
    repo_root = '/tmp/artman/%s' % task_id
    logger.info('Prepare a temporary root repo: %s' % repo_root)
    try:
        os.makedirs(repo_root)
    except OSError as e:
        raise e
    logger.info('Checking out fresh clone of %s.' % source_repo)
    googleapis_dir = os.path.join(repo_root, "googleapis")
    subprocess.check_output(['rm', '-f', '.git/config'])
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

    log_path = os.path.join(repo_root, 'artman.log')
    with io.open(log_path, 'w+') as file_:
        file_.write(u'-------- Beginning of %s -----------\n' % task_id)
    return task_id, repo_root, artman_user_config, log_path


def _cleanup(tmp_dir, log_file_handler):
    # Close the one-time logging FileHandler
    if log_file_handler:
        log_file_handler.close()

    # Pop all logging handlers.
    logger = logging.getLogger('artman')
    if logger.handlers:
        logger.handlers.pop()

    # Remove tmp directory.
    subprocess.check_call(['rm', '-rf', tmp_dir])

    # Change working directory to the root tmp directory, as the current one
    # has been removed.
    os.chdir('/tmp')
