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

from __future__ import print_function
import subprocess

from gcloud import logging as cloud_logging
from taskflow.task import Task


class TaskBase(Task):

    cloud_logger = None

    def __init__(self, *args, **kwargs):
        if 'inject' in kwargs and 'pipeline_id' in kwargs['inject']:
            pipeline_id = kwargs['inject']['pipeline_id']
            self.log_client = cloud_logging.Client()
            self.cloud_logger = self.log_client.logger(pipeline_id)
        super(TaskBase, self).__init__(*args, **kwargs)

    def validate(self):
        """Abstract method, which returns a list of task requirements.

        Subclass must implement this method and return a list of task
        requirements classes.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def log(self, msg):
        """Do local logging, and optionally cloud logging."""
        if self.cloud_logger:
            # TODO(ethanbao): Do batch logging.
            self.cloud_logger.log_text(msg)
        print(msg)

    def exec_command(self, args):
        """ Execute command and return output.

        TODO(ethanbao): Use subprocess.Popen which is recommended."""
        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
            if output:
                self.log(output)
            return output
        except subprocess.CalledProcessError as e:
            self.log(e.output)
            raise e


class EmptyTask(TaskBase):
    """An empty task that can be used by languages when they do not need to
    implement some functionality.
    """

    def execute(self):
        pass

    def validate(self):
        return []
