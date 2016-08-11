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

from pipeline.pipelines import code_generation_pipeline
from pipeline.tasks import protoc_tasks, package_tasks, publish_tasks


class GrpcClientPipeline(code_generation_pipeline.CodeGenerationPipelineBase):

    def __init__(self, **kwargs):
        super(GrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs)]

    def get_grpc_publish_tasks(self, **kwargs):
        return []

    def do_build_flow(self, **kwargs):
        flow = super(GrpcClientPipeline, self).do_build_flow(**kwargs)
        flow.add(*self.get_grpc_codegen_tasks(**kwargs))
        if 'publish_env' in kwargs:
            flow.add(*self.get_grpc_publish_tasks(**kwargs))
        return flow


class PythonGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'python'
        super(PythonGrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_publish_tasks(self, **kwargs):
        return [publish_tasks.PypiUploadTask('PypiUpload', inject=kwargs)]


class RubyGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'ruby'
        super(RubyGrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.GrpcPackmanTask('Packman', inject=kwargs),
                package_tasks.GrpcPackageDirTask('PackageDir', inject=kwargs),
                package_tasks.RubyPackageGenTask('GrpcPackageGen',
                                                 inject=kwargs)]


class NodeJSGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'nodejs'
        super(NodeJSGrpcClientPipeline, self).__init__(**kwargs)


class JavaGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        kwargs.update({'packman_flags': ['--experimental_alt_java']})
        super(JavaGrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_publish_tasks(self, **kwargs):
        return [publish_tasks.MavenDeployTask('MavenDeploy', inject=kwargs)]


class GoGrpcClientPipeline(GrpcClientPipeline):
    """Responsible for the protobuf/gRPC flow for Go language.

    The Go compiler needs to specify an import path which is relative to
    $GOPATH/src, otherwise it can't find the package. Therefore,
    the import path in proto files needs to be modified in this manner,
    which is taken care of by GoLangUpdateProtoImportsTask.
    """

    def __init__(self, **kwargs):
        kwargs['language'] = 'go'
        super(GoGrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_codegen_tasks(self, **kwargs):
        return [
            protoc_tasks.ProtoAndGrpcCodeGenTask('GrpcCodegen',
                                                 inject=kwargs),
            protoc_tasks.GoExtractImportBaseTask('ExtractGoPackageName',
                                                 inject=kwargs),
            protoc_tasks.GoLangUpdateImportsTask('UpdateImports',
                                                 inject=kwargs)]

    def validate_kwargs(self, **kwargs):
        code_generation_pipeline._validate_codegen_kwargs(
            ['gapic_api_yaml', 'final_repo_dir'],
            **kwargs)


class CSharpGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'csharp'
        super(CSharpGrpcClientPipeline, self).__init__(**kwargs)

    def get_grpc_codegen_tasks(self, **kwargs):
        return [protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs),
                protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs)]


class PhpGrpcClientPipeline(GrpcClientPipeline):

    def __init__(self, **kwargs):
        kwargs['language'] = 'php'
        super(PhpGrpcClientPipeline, self).__init__(**kwargs)
