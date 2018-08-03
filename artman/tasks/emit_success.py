# Copyright 2017 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import, unicode_literals
import os

from artman.tasks import task_base
from artman.utils.logger import logger


class EmitSuccess(task_base.TaskBase):
    """Emit a success message with the gapic_code_dir location."""

    def execute(self, gapic_code_dir, grpc_code_dir=None):
        """Emit a success message. No publishing is being done.

        Args:
            gapic_code_dir (str): The current GAPIC code location.
            grpc_code_dir (str): The current GRPC code location, if any.
        """
        userhome = os.path.expanduser('~')
        gapic_loc = os.path.realpath(gapic_code_dir).replace(userhome, '~')
        logger.success('Code generated: {0}'.format(gapic_loc))
        if grpc_code_dir:
            grpc_loc = os.path.realpath(grpc_code_dir).replace(userhome, '~')
            logger.success('GRPC code generated: {0}'.format(grpc_loc))


TASKS = (EmitSuccess,)
