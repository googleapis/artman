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
"""Utility functions related to tasks"""

import os.path
import re
import subprocess

import six


def get_gradle_task_output(task_name, task_path):
    task_path = os.path.realpath(os.path.expanduser(task_path))
    output = subprocess.check_output(['./gradlew', task_name], cwd=task_path)
    if isinstance(output, six.binary_type):
        output = output.decode('ascii')

    # It is a convention that gradle task uses 'output: ' as
    # prefix in their output
    prefix = 'output: '
    for line in output.split('\n'):
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def gradle_task(toolkit_path, task_name, task_args):
    """Generates a command for a gradle task."""
    toolkit_path = os.path.realpath(os.path.expanduser(toolkit_path))
    return [os.path.join(toolkit_path, 'gradlew'), '-p', toolkit_path,
            task_name, '-Pclargs=' + ','.join(task_args)]


def api_full_name(api_name, api_version, organization_name):
    """Canonical full name for an API; used to generate output directories and
    package name"""
    if api_version:
        return '-'.join([organization_name, api_name, api_version])
    else:
        return '-'.join([organization_name, api_name])


def packman_api_name(api_name):
    """Changes an pipeline kwarg API name to format expected by Packman"""
    return api_name.replace('-', '/')


def is_output_gcloud(language, gapic_code_dir):
    """Check if the gapic_code_dir is a part of gcloud project.
    """
    gapic_code_dir = os.path.abspath(gapic_code_dir)
    if language == 'nodejs':
        cloud_dirname = 'google-cloud-node'
    else:
        cloud_dirname = 'google-cloud-' + language
    if gapic_code_dir.find(os.path.sep + cloud_dirname + os.path.sep) >= 0:
        return True
    return re.search(os.path.sep + 'gcloud-[a-z]+' + os.path.sep,
                     gapic_code_dir)


def instantiate_tasks(task_class_list, inject):
    """Instantiates a list of Tasks. Generates a name for each task based on
    the class name, and if available the language and api_name settings.
    """
    tasks = []
    for task_class in task_class_list:
        name = task_class.__name__
        if inject.get('language'):
            name += '-' + inject['language']
        if inject.get('api_name'):
            name += '-' + inject['api_name']
        if inject.get('api_version'):
            name += '-' + inject['api_version']
        tasks.append(task_class(name, inject=inject))
    return tasks
