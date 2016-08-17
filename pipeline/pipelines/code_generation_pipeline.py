
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

import os
import time
import uuid

from pipeline.utils import pipeline_util
from pipeline.pipelines import pipeline_base
from pipeline.tasks import io_tasks
from taskflow.patterns import linear_flow


# TODO(garrettjones) fix required to be relative to pipeline.
# Ideally this should just be computed dynamically based
# on the pipeline's tasks.
def _validate_codegen_kwargs(extra_args, **kwargs):
    required = ['src_proto_path', 'import_proto_path', 'toolkit_path',
                'output_dir', 'language', 'api_name']
    pipeline_util.validate_exists(required + extra_args, **kwargs)


def _load_remote_parameters(kwargs):
    tmp_id = str(uuid.uuid4())
    filename = tmp_id + '.tar.gz'
    kwargs['tarfile'] = filename
    kwargs['bucket_name'] = 'pipeline'
    kwargs['src_path'] = filename
    kwargs['dest_path'] = time.strftime('%Y/%m/%d') + '/' + filename
    return kwargs


class CodeGenerationPipelineBase(pipeline_base.PipelineBase):
    """Base class for GAPIC, gRPC, and Core code generation pipelines, and
    for GAPIC config generation pipeline.
    """

    def __init__(self, task_factory, remote_mode=False, **kwargs):
        self.task_factory = task_factory
        if 'TOOLKIT_HOME' in os.environ:
            kwargs['toolkit_path'] = os.environ['TOOLKIT_HOME']
        if remote_mode:
            kwargs = _load_remote_parameters(kwargs)
        super(CodeGenerationPipelineBase, self).__init__(
            remote_mode=remote_mode, **kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('CodeGenerationPipeline')
        flow.add(io_tasks.PrepareGoogleapisDirTask('PrepareGoogleapisDirTask',
                                                   inject=kwargs))
        flow.add(*self.task_factory.get_tasks(**kwargs))
        return flow

    def additional_tasks_for_remote_execution(self, **kwargs):
        return [
            io_tasks.PrepareUploadDirTask('PrepareUploadDirTask',
                                          inject=kwargs),
            io_tasks.BlobUploadTask('BlobUploadTask', inject=kwargs),
            io_tasks.CleanupTempDirsTask('CleanupTempDirsTask',
                                         inject=kwargs)]

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(self.task_factory.get_validate_kwargs(),
                                 **kwargs)


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
