"""Pipelines that run gRPC codegen and VGen"""

import os
from pipeline.pipelines import pipeline_base
from pipeline.tasks import protoc_tasks, veneer_tasks, format_tasks
from pipeline.utils import pipeline_util
from taskflow.patterns import linear_flow


def _validate_gapi_tools_path(gapi_tools_path):
    if not (os.path.isfile(
                os.path.join(gapi_tools_path, 'gradlew')) and
            os.path.isfile(
                os.path.join(gapi_tools_path, 'build.gradle'))):
        raise ValueError(
                'gapi-tools does not contain `gradlew` or `build.gradle`'
                'at {0}'.format(gapi_tools_path))


# TODO(garrettjones) fix required to be relative to pipeline.
# Ideally this should just be computed dynamically based
# on the pipeline's tasks.
def _validate_codegen_kwargs(extra_args, **kwargs):
    required = ['src_proto_path',
                'import_proto_path',
                'gapi_tools_path',
                'output_dir',
                'language']
    pipeline_util.validate_exists(required + extra_args, **kwargs)
    _validate_gapi_tools_path(kwargs['gapi_tools_path'])


class PythonCodeGenPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'python'
        # TODO: Make generic.
        kwargs['package_name'] = 'logging/v2'
        super(PythonCodeGenPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('codegen')
        flow.add(protoc_tasks.ProtoAndGrpcCodeGenTask('GrpcCodegen',
                                                      inject=kwargs),
                 protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 protoc_tasks.PackmanTask('Packman', inject=kwargs),
                 veneer_tasks.VeneerCodeGenTask('VeneerCodegen',
                                                inject=kwargs),
                 format_tasks.PythonFormatTask('PythonFormat', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(['service_yaml', 'veneer_yaml'], **kwargs)


class JavaCorePipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaCorePipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('core-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class JavaGrpcClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaGrpcClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('grpc-codegen')
        flow.add(protoc_tasks.ProtoCodeGenTask('ProtoGen', inject=kwargs),
                 protoc_tasks.GrpcCodeGenTask('GrpcCodegen', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs([], **kwargs)


class JavaVkitClientPipeline(pipeline_base.PipelineBase):

    def __init__(self, **kwargs):
        kwargs['language'] = 'java'
        super(JavaVkitClientPipeline, self).__init__(**kwargs)

    def do_build_flow(self, **kwargs):
        flow = linear_flow.Flow('vkit-codegen')
        flow.add(protoc_tasks.ProtoDescGenTask('ProtoDesc', inject=kwargs),
                 veneer_tasks.VeneerCodeGenTask('VeneerCodegen',
                                                inject=kwargs),
                 format_tasks.JavaFormatTask('JavaFormat', inject=kwargs))
        return flow

    def validate_kwargs(self, **kwargs):
        _validate_codegen_kwargs(['service_yaml', 'veneer_yaml'], **kwargs)
