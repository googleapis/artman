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
from pipeline.tasks import protoc_tasks, package_tasks, publish_tasks


class GrpcClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GrpcClientPipeline, self).__init__(
            get_grpc_task_factory(kwargs['language']), **kwargs)


class GrpcTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        tasks = [protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs)]
        if 'publish_env' in kwargs:
            tasks.append(publish_tasks.make_publish_task(
                kwargs['language'], 'GrpcPublishTask', kwargs))
        return tasks

    def get_validate_kwargs(self):
        return []


class _RubyGrpcTaskFactory(GrpcTaskFactoryBase):

    def get_tasks(self, **kwargs):
        return [protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs),
                package_tasks.GrpcPackageDirTask('PackageDir', inject=kwargs),
                package_tasks.RubyPackageGenTask('GrpcPackageGen',
                                                 inject=kwargs)]


class _JavaGrpcTaskFactory(GrpcTaskFactoryBase):

    def get_tasks(self, **kwargs):
        kwargs.update({'packman_flags': ['--experimental_alt_java']})
        return super(_JavaGrpcTaskFactory, self).get_tasks(**kwargs)


class _GoGrpcTaskFactory(GrpcTaskFactoryBase):
    """Responsible for the protobuf/gRPC flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.
    """

    def get_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask('GrpcCodegen',
                                                 inject=kwargs),
            protoc_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                 inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs)]

    def get_validate_kwargs(self):
        return ['gapic_api_yaml', 'final_repo_dir']


class _CSharpGrpcTaskFactory(GrpcTaskFactoryBase):

    def get_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs),
                protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs)]


_GRPC_TASK_FACTORY_DICT = {
    'java': _JavaGrpcTaskFactory,
    'python': GrpcTaskFactoryBase,
    'go': _GoGrpcTaskFactory,
    'ruby': _RubyGrpcTaskFactory,
    'php': GrpcTaskFactoryBase,
    'csharp': _CSharpGrpcTaskFactory,
    'nodejs': GrpcTaskFactoryBase
}


def get_grpc_task_factory(language):
    cls = _GRPC_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No gRPC task factory found for language: '
                         + language)
