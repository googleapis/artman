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
from pipeline.tasks import task_base
from pipeline.tasks.requirements import go_requirements
from pipeline.tasks.requirements import ruby_requirements
from pipeline.utils import task_utils


# TODO: Store both intermediate and final output in all format tasks.

class JavaFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir, toolkit_path):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        # TODO(shinfan): Move gradle task into requirement
        path = task_utils.runGradleTask(
                'showJavaFormatterPath', toolkit_path)
        targetFiles = []
        for root, dirs, files in os.walk(intermediate_code_dir):
            for filename in files:
                if filename.endswith('.java'):
                    targetFile = os.path.abspath(os.path.join(root, filename))
                    targetFiles.append(targetFile)
        subprocess.check_call(
            ['java', '-jar', path, '--replace'] + targetFiles)

    def validate(self):
        return []


class PythonFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        targetFiles = []
        for root, dirs, files in os.walk(intermediate_code_dir):
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
    def execute(self, intermediate_code_dir):
        print 'Formatting files in ' + os.path.abspath(intermediate_code_dir)
        subprocess.check_call(['gofmt', '-w', intermediate_code_dir])

    def validate(self):
        return [go_requirements.GoFormatRequirements]


class RubyFormatTask(task_base.TaskBase):
    def execute(self, intermediate_code_dir):
        print 'Formatting file in ' + os.path.abspath(intermediate_code_dir)
        subprocess.call(['rubocop', '-a', intermediate_code_dir])

    def validate(self):
        return [ruby_requirements.RubyFormatRequirements]
