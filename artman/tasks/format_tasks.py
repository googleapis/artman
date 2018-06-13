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

import os
import subprocess

from artman.tasks import task_base
from artman.utils import task_utils
from artman.utils.logger import logger


# TODO: Store both intermediate and final output in all format tasks.

class JavaFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir, toolkit_path):
        logger.debug('Formatting files in %s.' %
                    os.path.abspath(gapic_code_dir))
        path = task_utils.get_java_tool_path(toolkit_path, 'googleJavaFormatJar')
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
        logger.debug('Formatting files in %s.' %
                    os.path.abspath(gapic_code_dir))
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
        logger.debug('Formatting files in %s.' %
                    os.path.abspath(gapic_code_dir))
        self.exec_command(['gofmt', '-w', gapic_code_dir])


class PhpFormatTask(task_base.TaskBase):
    def execute(self, gapic_code_dir):
        abs_code_dir = os.path.abspath(gapic_code_dir)
        logger.debug('Formatting file using php-cs-fixer in %s.' % abs_code_dir)
        subprocess.call(['php-cs-fixer', 'fix',
                         '--rules=@Symfony,-phpdoc_annotation_without_dot',
                         gapic_code_dir])
        # We require a second call to php-cs-fixer because instances of @type
        # have been converted to @var. We cannot disable this conversion in
        # the first call without affecting other aspects of the formatting.
        subprocess.call(['php-cs-fixer',
                         'fix',
                         '--rules={"phpdoc_no_alias_tag" : {"replacements" : '
                         '{"var" : "type"}}}',
                         gapic_code_dir])
        logger.debug('Formatting file using phpcbf in %s.' % abs_code_dir)
        subprocess.call(['phpcbf', '--standard=PSR2', '--no-patch',
                         gapic_code_dir])


_FORMAT_TASK_DICT = {
    'java': JavaFormatTask,
    'python': PythonFormatTask,
    'go': GoFormatTask,
    'php': PhpFormatTask,
}


def get_format_task(language):
    return _FORMAT_TASK_DICT.get(language, task_base.EmptyTask)
