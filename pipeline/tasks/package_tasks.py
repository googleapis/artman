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

"""Tasks related to packages of the languages."""

import os
import subprocess

from pipeline.tasks import task_base
from pipeline.tasks.requirements import ruby_requirements


def _scoped_run_command(target_dir, commands):
    current_dir = os.getcwd()
    os.chdir(target_dir)
    subprocess.check_output(commands, stderr=subprocess.STDOUT)
    os.chdir(current_dir)


class RubyPackageGenTask(task_base.TaskBase):
    """Generates .gem file for the target directory."""

    def execute(self, package_dir):
        _scoped_run_command(package_dir, ['rake', 'build'])

    def validate(self):
        return [ruby_requirements.RakeRequirements]


class GrpcPackageDirTask(task_base.TaskBase):
    """Bring 'package_dir' parameter for gRPC code generation pipeline.

    This assumes that gRPC client is generated through packman, which generates
    the files under output/language.
    """

    default_provides = 'package_dir'

    def execute(self, language, output_dir):
        return os.path.join(output_dir, language)


class GapicPackageDirTask(task_base.TaskBase):
    """Bring 'package_dir' parameter for Gapic code generation pipeline."""

    default_provides = 'package_dir'

    def execute(self, final_repo_dir):
        return final_repo_dir
