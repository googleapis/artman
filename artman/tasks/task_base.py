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

"""Base class for pipeline task.

This base class extends taskflow Task class, with additional methods and
properties used by the GAPIC pipeline."""

import logging
import subprocess

from gcloud import logging as cloud_logging

from taskflow.task import Task

from artman.utils.logger import logger as artman_logger
from artman.utils.logger import output_logger
from artman.utils.logger import OUTPUT


class TaskBase(Task):

    cloud_logger = None

    def __init__(self, *args, **kwargs):
        super(TaskBase, self).__init__(*args, **kwargs)

    def validate(self):
        """Abstract method, which returns a list of task requirements.

        Subclass must implement this method and return a list of task
        requirements classes.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def log(self, msg, logger=artman_logger, level=logging.INFO):
        """Do local logging, and optionally cloud logging.

        Args:
            msg (str): The message to be logged.
            logger (logging.Logger): The logger to use. This defaults to
                logging.getLogger('artman').
            level (int): The log level. Defaults to logging.INFO.
        """
        logger.log(level, msg)

    def exec_command(self, args):
        """ Execute command and return output.

        TODO(ethanbao): Use subprocess.Popen which is recommended."""
        try:
            self.log(' '.join(args), level=logging.DEBUG)
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
            if output:
                output = output.decode('utf8')
                self.log(output, logger=output_logger, level=OUTPUT)
            return output
        except subprocess.CalledProcessError as e:
            self.log(e.output, logger=output_logger, level=logging.ERROR)
            raise e


class EmptyTask(TaskBase):
    """An empty task that can be used by languages when they do not need to
    implement some functionality.
    """
    def execute(self):
        pass

    def validate(self):
        return []
