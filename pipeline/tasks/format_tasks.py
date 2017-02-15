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

"""Tasks related to format"""

from __future__ import print_function
import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import go_requirements
from pipeline.tasks.requirements import php_requirements
from pipeline.utils import task_utils


# TODO: Store both intermediate and final output in all format tasks.

class JavaFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir, toolkit_path):
        print('Formatting files in %s.' % os.path.abspath(gapic_code_dir))
        # TODO(shinfan): Move gradle task into requirement
        path = task_utils.get_gradle_task_output(
                'showJavaFormatterPath', toolkit_path)
        targetFiles = []
        for root, dirs, files in os.walk(gapic_code_dir):
            for filename in files:
                if filename.endswith('.java'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        self.exec_command(
            ['java', '-jar', path, '--replace'] + targetFiles)

    def validate(self):
        return []


class PythonFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir):
        print('Formatting files in %s.' % os.path.abspath(gapic_code_dir))
        targetFiles = []
        for root, dirs, files in os.walk(gapic_code_dir):
            for filename in files:
                if filename.endswith('.py'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        # yapf returns code 2 when it formats, so we can't use `check_call`.
        exit_code = subprocess.call(['yapf', '-i'] + targetFiles)
        if exit_code not in [0, 2]:
            raise subprocess.CalledProcessError(exit_code, 'yapf')

    # yapf is installed by tox for the entire pipeline project's virtualenv,
    # so we shouldn't need a separate validation task.
    def validate(self):
        return []


class GoFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir):
        print('Formatting files in %s.' % os.path.abspath(gapic_code_dir))
        self.exec_command(['gofmt', '-w', gapic_code_dir])

    def validate(self):
        return [go_requirements.GoFormatRequirements]


class PhpFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir):
        abs_code_dir = os.path.abspath(gapic_code_dir)
        print('Formatting file using php-cs-fixer in %s.' % abs_code_dir)
        subprocess.call(['php-cs-fixer', 'fix', gapic_code_dir])
        # We require a second call to php-cs-fixer because instances of @type
        # have been converted to @var. We cannot disable this conversion in
        # the first call without affecting other aspects of the formatting.
        subprocess.call(['php-cs-fixer', 'fix', gapic_code_dir,
                         '--fixers=phpdoc_var_to_type'])
        print('Formatting file using phpcbf in %s.' % abs_code_dir)
        subprocess.call(['phpcbf', '--standard=PSR2', gapic_code_dir])

    def validate(self):
        return [php_requirements.PhpFormatRequirements]


_FORMAT_TASK_DICT = {
    'java': JavaFormatTask,
    'python': PythonFormatTask,
    'go': GoFormatTask,
    'ruby': task_base.EmptyTask,
    'php': PhpFormatTask,
    'csharp': task_base.EmptyTask,
    'nodejs': task_base.EmptyTask
}


def get_format_task(language):
    cls = _FORMAT_TASK_DICT.get(language)
    if cls:
        return cls
    else:
        raise ValueError('No format task found for language: ' + language)
