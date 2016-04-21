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
properties used by GAPIC pipeline."""

from taskflow.task import Task


class TaskBase(Task):

    def validate(self):
        """Abstract method, which returns list of task requirements.

        Subclass must implment this method and return list of task requirements
        classes.
        """
        raise NotImplementedError("Subclass must implement abstract method")
