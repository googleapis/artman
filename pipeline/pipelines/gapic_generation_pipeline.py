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
                  'auto_merge', 'auto_resolve', 'ignore_base',
                  'final_repo_dir']


class GapicConfigPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = ''
        super(GapicConfigPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = super(GapicConfigPipeline, self).do_build_flow(**kwargs)
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 gapic_tasks.GapicConfigGenTask(
                     'GapicConfigGen', inject=kwargs),
                 gapic_tasks.GapicConfigMoveTask(
                     'GapicConfigMove', inject=kwargs))
        return flow


class GapicClientPipelineBase(code_gen.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GapicClientPipelineBase, self).__init__(**kwargs)

    def get_gapic_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                gapic_tasks.GapicCodeGenTask('GapicCodegen', inject=kwargs),
                format_tasks.make_format_task(
                    kwargs['language'], 'GapicFormat', kwargs)]

    def get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicMergeTask('GapicMerge', inject=kwargs)]

    def do_build_flow(self, **kwargs):
        flow = super(GapicClientPipelineBase, self).do_build_flow(**kwargs)
        flow.add(*self.get_gapic_codegen_tasks(**kwargs))
        flow.add(*self.get_gapic_package_tasks(**kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        code_gen._validate_codegen_kwargs(_VGEN_REQUIRED, **kwargs)


class PythonGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'python'
        super(PythonGapicClientPipeline, self).__init__(**kwargs)

    def get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicCopyTask('GapicCopy', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs)]


class RubyGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'ruby'
        super(RubyGapicClientPipeline, self).__init__(**kwargs)

    def get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicMergeTask('GapicMerge', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs),
                package_tasks.GapicPackageDirTask('PackageDir',
                                                  inject=kwargs),
                package_tasks.RubyPackageGenTask('GapicPackageGen',
                                                 inject=kwargs)]


class NodeJSGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'nodejs'
        super(NodeJSGapicClientPipeline, self).__init__(**kwargs)

    def get_gapic_package_tasks(self, **kwargs):
        return [gapic_tasks.GapicMergeTask('GapicMerge', inject=kwargs),
                gapic_tasks.GapicPackmanTask('GapicPackman', inject=kwargs)]


class JavaGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaGapicClientPipeline, self).__init__(**kwargs)


class GoGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'go'
        super(GoGapicClientPipeline, self).__init__(**kwargs)


class CSharpGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpGapicClientPipeline, self).__init__(**kwargs)

    def get_gapic_package_tasks(self, **kwargs):
        return []


class PhpGapicClientPipeline(GapicClientPipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'php'
        super(PhpGapicClientPipeline, self).__init__(**kwargs)
