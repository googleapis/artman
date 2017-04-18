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

"""Tasks that perform cleanup after code generation"""

import os
import subprocess

from artman.tasks import task_base
from artman.utils.logger import logger


class CleanUpTask(task_base.TaskBase):
    """Recursively removes all entries in `output_dir` that are not included in
    `saved_dirs`"""
    def execute(self, output_dir, saved_dirs):
        logger.info('Cleaning up temporary files.')
        for entry in os.listdir(output_dir):
            if entry not in saved_dirs:
                subprocess.check_call(
                    ['rm', '-rf', os.path.join(output_dir, entry)])

    def validate(self):
        return []
