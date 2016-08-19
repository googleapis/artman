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

"""Pipelines that run GAPIC"""

from pipeline.pipelines import code_generation_pipeline as code_gen
from pipeline.tasks import gapic_tasks, format_tasks, protoc_tasks
from pipeline.tasks import package_tasks


# kwargs required by GAPIC code gen
_VGEN_REQUIRED = ['service_yaml', 'gapic_language_yaml', 'gapic_api_yaml',
                  'final_repo_dir']


class GapicConfigPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicConfigPipeline, self).__init__(
            GapicConfigTaskFactory(), **kwargs)


class GapicConfigTaskFactory(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return [protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                gapic_tasks.GapicConfigGenTask(
                     'GapicConfigGen', inject=kwargs),
                gapic_tasks.GapicConfigMoveTask(
                     'GapicConfigMove', inject=kwargs)]

    def get_validate_kwargs(self):
        return []


class GapicClientPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicClientPipeline, self).__init__(
            get_gapic_task_factory(kwargs['language']),
            **kwargs)


class GapicTaskFactoryBase(code_gen.TaskFactoryBase):

    def get_tasks(self, **kwargs):
        return (self._get_gapic_codegen_tasks(**kwargs)
                + self._get_gapic_package_tasks(**kwargs))

    def _get_gapic_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                gapic_tasks.GapicCodeGenTask('GapicCodegen', inject=kwargs),
                format_tasks.make_format_task(
                    kwargs['language'], 'GapicFormat', kwargs)]

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask('GapicCopy', inject=kwargs)]

    def get_validate_kwargs(self):
        return _VGEN_REQUIRED


class _PythonGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCleanTask('GapicClean', inject=kwargs),
                gapic_tasks.GapicCopyTask('GapicCopy', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs)]


class _RubyGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask('GapicCopy', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs),
                package_tasks.RubyPackageGenTask('GapicPackageGen',
                                                 inject=kwargs)]


class _NodeJSGapicTaskFactory(GapicTaskFactoryBase):

    def _get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask('GapicCopy', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs)]


_GAPIC_TASK_FACTORY_DICT = {
    'java': GapicTaskFactoryBase,
    'python': _PythonGapicTaskFactory,
    'go': GapicTaskFactoryBase,
    'ruby': _RubyGapicTaskFactory,
    'php': GapicTaskFactoryBase,
    'csharp': GapicTaskFactoryBase,
    'nodejs': _NodeJSGapicTaskFactory
}


def get_gapic_task_factory(language):
    cls = _GAPIC_TASK_FACTORY_DICT.get(language)
    if cls:
        return cls()
    else:
        raise ValueError('No GAPIC task factory found for language: '
                         + language)
