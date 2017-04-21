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

from artman.pipelines import batch_generation as batch_gen
from artman.pipelines import code_generation as code_gen
from artman.tasks import package_metadata_tasks
from artman.tasks import protoc_tasks
from artman.tasks import publish
from artman.tasks import python_grpc_tasks
from artman.tasks import staging_tasks
from artman.utils import task_utils


class GrpcClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GrpcClientPipeline, self).__init__(
            _get_grpc_task_factory(kwargs), **kwargs)


class ProtoClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(ProtoClientPipeline, self).__init__(
            _get_proto_task_factory(kwargs), **kwargs)


class GrpcTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        tasks = self._get_grpc_codegen_tasks(**kwargs)
        return task_utils.instantiate_tasks(tasks, kwargs)

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.GrpcPackmanTask]

    def _get_grpc_staging_tasks(self, **kwargs):
        if kwargs['stage_output']:
            return [staging_tasks.StagingGrpcOutputDirTask,
                    staging_tasks.StagingCleanTask,
                    staging_tasks.StagingCopyTask]
        return []

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class GrpcClientBatchPipeline(batch_gen.BatchPipeline):

    def __init__(self, **kwargs):
        super(GrpcClientBatchPipeline, self).__init__(
            _make_batch_pipeline_tasks, **kwargs)


def _make_batch_pipeline_tasks(**kwargs):
    task_factory = _get_grpc_task_factory(kwargs)
    tasks = (task_factory._get_grpc_codegen_tasks(**kwargs)
             + task_factory._get_grpc_staging_tasks(**kwargs))
    return task_utils.instantiate_tasks(tasks, kwargs)


class _RubyGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            protoc_tasks.RubyGrpcCopyTask,
        ]


class _JavaGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoDescGenTask,
            protoc_tasks.GrpcCodeGenTask,
            package_metadata_tasks.JavaGrpcPackageTypeTask,
            package_metadata_tasks.PackageMetadataConfigGenTask,
            package_metadata_tasks.ProtoPackageMetadataGenTask,
        ]


class _JavaProtoTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoDescGenTask,
            protoc_tasks.ProtoCodeGenTask,
            package_metadata_tasks.JavaProtoPackageTypeTask,
            package_metadata_tasks.PackageMetadataConfigGenTask,
            package_metadata_tasks.ProtoPackageMetadataGenTask,
        ]


class _PythonGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            python_grpc_tasks.PythonChangePackageTask,
            protoc_tasks.ProtoDescGenTask,
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            package_metadata_tasks.PackageMetadataConfigGenTask,
            package_metadata_tasks.ProtoPackageMetadataGenTask,
        ]


class _GoGrpcTaskFactory(GrpcTaskFactoryBase):
    """Responsible for the protobuf/gRPC flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.
    """

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            protoc_tasks.GoExtractImportBaseTask,
            protoc_tasks.GoLangUpdateImportsTask,
        ]

    def get_validate_kwargs(self):
        return ['gapic_api_yaml', 'gapic_code_dir'] + code_gen.COMMON_REQUIRED


class _CSharpGrpcTaskFactory(GrpcTaskFactoryBase):

    def _get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoCodeGenTask,
            protoc_tasks.GrpcCodeGenTask,
        ]


_GRPC_TASK_FACTORY_DICT = {
    'java': _JavaGrpcTaskFactory,
    'python': _PythonGrpcTaskFactory,
    'go': _GoGrpcTaskFactory,
    'ruby': _RubyGrpcTaskFactory,
    'php': GrpcTaskFactoryBase,
    'csharp': _CSharpGrpcTaskFactory,
    'nodejs': GrpcTaskFactoryBase,
}


_PROTO_TASK_FACTORY_DICT = {
    'java': _JavaProtoTaskFactory,
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


def _get_proto_task_factory(kwargs):
    if 'language' not in kwargs:
        raise ValueError('Valid --language argument required for gRPC codegen')

    language = kwargs['language']
    cls = _PROTO_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No proto task factory found for language: '
                         + language)
