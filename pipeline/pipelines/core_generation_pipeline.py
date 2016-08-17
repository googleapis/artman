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

"""Pipelines that run protoc core codegen. The generated core library for each
language contains the well known types, defined by protobuf, for that language.
"""

from pipeline.pipelines import code_generation_pipeline as code_gen
from pipeline.pipelines import grpc_generation_pipeline
from pipeline.tasks import protoc_tasks


class CoreProtoPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(CoreProtoPipeline, self).__init__(
            get_core_task_factory(kwargs['language']), **kwargs)


class _JavaCoreTaskFactory(grpc_generation_pipeline.GrpcTaskFactoryBase):
    """Generates a package with the common protos from googleapis.

    It inherits from GrpcTaskFactoryBase because it uses Packman just like
    client generation does; the only difference is the extra
    --build_common_protos argument to Packman.
    """

    def get_tasks(self, **kwargs):
        packman_flags = ['--experimental_alt_java', '--build_common_protos']
        kwargs.update({'packman_flags': packman_flags})
        return super(_JavaCoreTaskFactory, self).get_tasks(**kwargs)


class _GoCoreTaskFactory(code_gen.TaskFactoryBase):
    """Responsible for the protobuf flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.

    TODO(mukai): Remove this flow once the repository for well-known types is
    set up.
    """

    def get_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoCodeGenTask('CoreProtoGen',
                                          inject=kwargs),
            protoc_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                 inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs)]

    def get_validate_kwargs(self):
        return ['gapic_api_yaml', 'final_repo_dir']


class _CSharpCoreTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs)]

    def get_validate_kwargs(self):
        return []


_CORE_TASK_FACTORY_DICT = {
    'java': _JavaCoreTaskFactory,
    'go': _GoCoreTaskFactory,
    'csharp': _CSharpCoreTaskFactory,
}


def get_core_task_factory(language):
    cls = _CORE_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No core task factory found for language: '
                         + language)
