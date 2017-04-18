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

"""Requirements classes related to Go."""

from __future__ import absolute_import
import os

from artman.tasks.requirements import task_requirement_base


class GoPathRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def install(cls):
        # Intentionally do nothing.
        pass

    @classmethod
    def require(cls):
        # Intentionally do nothing.
        return []

    @classmethod
    def is_installed(cls):
        return 'GOPATH' in os.environ


class GoFormatRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def install(cls):
        pass

    @classmethod
    def require(cls):
        return ['gofmt']
