
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

"""Base class for code generation pipelines."""

import time
import uuid
import importlib

from artman.utils import task_utils
from artman.pipelines import pipeline_base
from artman.tasks import io_tasks
from taskflow.patterns import linear_flow


# kwargs required by multiple pipelines
COMMON_REQUIRED = ['src_proto_path', 'import_proto_path', 'toolkit_path', 'root_dir',
                   'output_dir', 'api_name', 'api_version',
                   'organization_name']

COMMON_DISCO_REQUIRED = ['discovery_doc', 'toolkit_path', 'root_dir', 'output_dir',
                         'api_name', 'api_version', 'organization_name']


class CodeGenerationPipelineBase(pipeline_base.PipelineBase):
    """Base class for GAPIC, gRPC, and Core code generation pipelines, and
    for GAPIC config generation pipeline.
    """
    def __init__(self, task_factory, **kwargs):
        self.task_factory = task_factory
        super(CodeGenerationPipelineBase, self).__init__(
            **kwargs)

    def do_build_flow(self, **kwargs):
        tasks = task_utils.instantiate_tasks(
            [io_tasks.PrepareGoogleapisDirTask], kwargs)
        tasks += self.task_factory.get_tasks(**kwargs)
        flow = linear_flow.Flow('CodeGenerationPipeline')
        flow.add(*tasks)
        return flow

    def validate_kwargs(self, **kwargs):
        # TODO(garrettjones) fix required to be relative to pipeline.
        # Ideally this should just be computed dynamically based
        # on the pipeline's tasks.
        _validate_exists(self.task_factory.get_validate_kwargs(),
                                      **kwargs)
        _validate_does_not_exist(
            self.task_factory.get_invalid_kwargs(), **kwargs)


class TaskFactoryBase(object):
    """Abstract base class for task factories.

    Task factory objects are used by CodeGenerationPipelineBase.
    Subclasses must implement the get_tasks and get_validate_kwargs
    methods.
    """

    def get_tasks(self, **kwargs):
        """Abstract method, subclasses must implement this method and return
        a list of tasks.
        """
        raise NotImplementedError('Subclass must implement abstract method')

    def get_validate_kwargs(self):
        """Abstract method, subclasses must implement this method and return
        a list of required keyword arguments.
        """
        raise NotImplementedError('Subclass must implement abstract method')

    def get_invalid_kwargs(self):
        """Abstract method, subclasses must implement this method and return
        a list of required keyword arguments.
        """
        raise NotImplementedError('Subclass must implement abstract method')


def _validate_exists(required, **kwargs):
    for arg in required:
        if arg not in kwargs:
            raise ValueError('{0} must be provided'.format(arg))


def _validate_does_not_exist(unsupported, **kwargs):
    for arg in unsupported:
        if arg in kwargs:
            raise ValueError('{0} is not supported'.format(arg))
