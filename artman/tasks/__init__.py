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

"""Module containing all artman tasks.

This module provides all tasks from its submodules.
It drops all "_tasks" suffices from the submodule names, which will allow
us to move to a clearer and more succinct spelling: `tasks.{domain}.{name}`
"""

from __future__ import absolute_import

from artman.tasks import emit_success as success
from artman.tasks import format_tasks as format
from artman.tasks import gapic_tasks as gapic
from artman.tasks import io_tasks as io
from artman.tasks import package_metadata_tasks as package_metadata
from artman.tasks import protoc_tasks as protoc
from artman.tasks import python_grpc_tasks as python_grpc
from artman.tasks.task_base import Task, EmptyTask

__all__ = (
    'EmptyTask', 'format', 'gapic', 'io',
    'package_metadata', 'protoc', 'python_grpc', 'success'
    'Task',
)
