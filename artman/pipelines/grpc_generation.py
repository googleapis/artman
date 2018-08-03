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

from artman.pipelines import code_generation as code_gen
from artman.tasks import emit_success
from artman.tasks import package_metadata_tasks
from artman.tasks import protoc_tasks
from artman.tasks import python_grpc_tasks
from artman.utils import task_utils


class GrpcClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GrpcClientPipeline, self).__init__(
            ProtoGenTaskFactory(gen_grpc=True, **kwargs), **kwargs)


class ProtoClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(ProtoClientPipeline, self).__init__(
            ProtoGenTaskFactory(gen_grpc=False, **kwargs), **kwargs)


class ProtoGenTaskFactory(code_gen.TaskFactoryBase):

    def __init__(self, gen_grpc, **kwargs):
        if 'language' not in kwargs:
            raise ValueError('Valid `language` argument required for gRPC codegen')
        if 'aspect' not in kwargs:
            raise ValueError('Valid `aspect` argument required for gRPC codegen')
        self.language = kwargs['language']
        self.gen_grpc = gen_grpc
        self.gen_code = kwargs['aspect'] == 'ALL' or kwargs['aspect'] == 'CODE'
        self.gen_pkg = kwargs['aspect'] == 'ALL' or kwargs['aspect'] == 'PACKAGE'

    def get_tasks(self, **kwargs):
        tasks = self.get_grpc_codegen_tasks(**kwargs)
        tasks += emit_success.TASKS
        return task_utils.instantiate_tasks(tasks, kwargs)

    def get_grpc_codegen_tasks(self, **kwargs):
        methods = {
            'java': self._get_grpc_codegen_tasks_java,
            'python': self._get_grpc_codegen_tasks_python,
            'go': self._get_grpc_codegen_tasks_go,
            'ruby': self._get_grpc_codegen_tasks_ruby,
            'php': self._get_grpc_codegen_tasks_php,
            'csharp': self._get_grpc_codegen_tasks_csharp,
            'nodejs': self._get_grpc_codegen_tasks_nodejs
        }
        return methods[self.language](**kwargs)

    def _get_grpc_codegen_tasks_java(self, **kwargs):
        tasks = [protoc_tasks.ProtoDescGenTask]
        if self.gen_code:
            tasks.append(protoc_tasks.ProtoCodeGenTask)
            if self.gen_grpc:
                tasks.append(protoc_tasks.GrpcCodeGenTask)
        tasks.append(package_metadata_tasks.PackageMetadataConfigGenTask)
        if self.gen_pkg:
            tasks.append(package_metadata_tasks.ProtoPackageMetadataGenTask)
            if self.gen_grpc:
                tasks.append(package_metadata_tasks.GrpcPackageMetadataGenTask)
        tasks.append(protoc_tasks.JavaProtoCopyTask)
        return tasks

    def _get_grpc_codegen_tasks_python(self, **kwargs):
        tasks = [python_grpc_tasks.PythonChangePackageTask]
        tasks.append(protoc_tasks.ProtoDescGenTask)
        if self.gen_code:
            tasks.append(protoc_tasks.ProtoAndGrpcCodeGenTask)
        if self.gen_pkg:
            tasks.append(package_metadata_tasks.PackageMetadataConfigGenTask)
        tasks.append(python_grpc_tasks.PythonMoveProtosTask)
        return tasks

    def _get_grpc_codegen_tasks_go(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            protoc_tasks.GoCopyTask,
        ]

    def _get_grpc_codegen_tasks_ruby(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            protoc_tasks.RubyGrpcCopyTask,
        ]

    def _get_grpc_codegen_tasks_php(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask,
            protoc_tasks.PhpGrpcRenameTask,
            protoc_tasks.PhpGrpcMoveTask,
        ]
    def _get_grpc_codegen_tasks_csharp(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask, protoc_tasks.GrpcCodeGenTask]

    def _get_grpc_codegen_tasks_nodejs(self, **kwargs):
        return [protoc_tasks.NodeJsProtoCopyTask]

    def get_validate_kwargs(self):
        if self.language == 'go':
            return ['gapic_yaml', 'gapic_code_dir'] + code_gen.COMMON_REQUIRED
        else:
            return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []
