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

"""Pipelines that run gRPC codegen"""

from pipeline.pipelines import code_generation_pipeline as code_gen
from pipeline.tasks import (package_metadata_tasks, protoc_tasks,
                            publish_tasks, python_grpc_tasks)
from pipeline.utils import task_utils


class GrpcClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GrpcClientPipeline, self).__init__(
            _get_grpc_task_factory(kwargs), **kwargs)


class GrpcTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        tasks = self._get_grpc_codegen_tasks(**kwargs)
        if 'publish_env' in kwargs:
            tasks.append(publish_tasks.get_publish_task(
                kwargs['language']))
        return task_utils.instantiate_tasks(tasks, kwargs)

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.GrpcPackmanTask]

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class _RubyGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoAndGrpcCodeGenTask,
                protoc_tasks.RubyGrpcCopyTask]


class _JavaGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.JavaGrpcPackmanTask]


class _PythonGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [python_grpc_tasks.PythonChangePackageTask,
                protoc_tasks.ProtoDescGenTask,
                protoc_tasks.ProtoAndGrpcCodeGenTask,
                package_metadata_tasks.GrpcPackageMetadataGenTask]


class _GoGrpcTaskFactory(GrpcTaskFactoryBase):
    """Responsible for the protobuf/gRPC flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.
    """

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoAndGrpcCodeGenTask,
                protoc_tasks.GoExtractImportBaseTask,
                protoc_tasks.GoLangUpdateImportsTask]

    def get_validate_kwargs(self):
        return ['gapic_api_yaml', 'final_repo_dir'] + code_gen.COMMON_REQUIRED


class _CSharpGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask,
                protoc_tasks.GrpcCodeGenTask]


_GRPC_TASK_FACTORY_DICT = {
    'java': _JavaGrpcTaskFactory,
    'python': _PythonGrpcTaskFactory,
    'go': _GoGrpcTaskFactory,
    'ruby': _RubyGrpcTaskFactory,
    'php': GrpcTaskFactoryBase,
    'csharp': _CSharpGrpcTaskFactory,
    'nodejs': GrpcTaskFactoryBase
}


def _get_grpc_task_factory(kwargs):
    if 'language' not in kwargs:
        raise ValueError('Valid --language argument required for gRPC codegen')

    language = kwargs['language']
    cls = _GRPC_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No gRPC task factory found for language: '
                         + language)
