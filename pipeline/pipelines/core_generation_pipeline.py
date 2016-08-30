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
from pipeline.tasks import protoc_tasks, publish_tasks
from pipeline.utils import task_utils


class CoreProtoPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(CoreProtoPipeline, self).__init__(
            get_core_task_factory(kwargs['language']), **kwargs)


class CoreTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return task_utils.instantiate_tasks(
            self._get_core_codegen_tasks(**kwargs), kwargs)

    def _get_core_codegen_tasks(self, **kwargs):
        raise NotImplementedError('Subclass must implement abstract method')

    def get_validate_kwargs(self):
        return code_gen.COMMON_REQUIRED

    def get_invalid_kwargs(self):
        return []


class _JavaCoreTaskFactory(CoreTaskFactoryBase):
    """Generates a package with the common protos from googleapis.
    """

    def _get_core_codegen_tasks(self, **kwargs):
        tasks = [protoc_tasks.JavaCorePackmanTask]
        if 'publish_env' in kwargs:
            tasks.append(publish_tasks.MavenDeployTask)
        return tasks


class _GoCoreTaskFactory(CoreTaskFactoryBase):
    """Responsible for the protobuf flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.

    TODO(mukai): Remove this flow once the repository for well-known types is
    set up.
    """

    def _get_core_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask,
                protoc_tasks.GoExtractImportBaseTask,
                protoc_tasks.GoLangUpdateImportsTask]

    def get_validate_kwargs(self):
        return ['gapic_api_yaml', 'final_repo_dir'] + code_gen.COMMON_REQUIRED


class _CSharpCoreTaskFactory(CoreTaskFactoryBase):

    def _get_core_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask]


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
