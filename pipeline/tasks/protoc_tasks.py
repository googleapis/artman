"""Tasks related to protoc"""

import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements
from pipeline.tasks.requirements import packman_requirements
from pipeline.utils import lang_params
from pipeline.utils import task_utils


class _PythonProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['python']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir):
        return '--python_out=' + self.code_root(output_dir)

    def grpc_plugin_path(self, dummy_gapi_tools_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'grpc_python_plugin'])[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)


class _JavaProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['java']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir):
        return '--java_out=' + self.code_root(output_dir)

    def grpc_plugin_path(self, gapi_tools_path):
        if self.path is None:
            print 'start gradle process to locate GRPC Java plugin'
            self.path = task_utils.runGradleTask(
                'showGrpcJavaPluginPath', gapi_tools_path, 'protoc-gen-grpc-java')
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

_PROTO_PARAMS_MAP = {
    'python': _PythonProtoParams(),
    'java': _JavaProtoParams()
}


def _find_protos(proto_paths):
    """Searches along `proto_path` for .proto files and returns a list of
    paths"""
    protos = []
    if type(proto_paths) is not list:
        raise ValueError("proto_paths must be a list")
    for path in proto_paths:
        for root, _, files in os.walk(path):
            protos += [os.path.join(root, proto) for proto in files
                       if os.path.splitext(proto)[1] == '.proto']
    return protos


def _protoc_header_params(import_proto_path, src_proto_path):
    return (['protoc'] +
            ['--proto_path=' + path for path in
             (import_proto_path + src_proto_path)])


def _protoc_desc_params(output_dir, desc_out_file):
    return (['--include_imports',
             '--include_source_info',
             '-o', os.path.join(output_dir, desc_out_file)])


def _protoc_proto_params(proto_params, pkg_dir):
    return [proto_params.lang_out_param(pkg_dir)]


def _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path):
    return (['--plugin=protoc-gen-grpc=' +
             proto_params.grpc_plugin_path(gapi_tools_path),
             proto_params.grpc_out_param(pkg_dir)])


def _prepare_pkg_dir(output_dir, api_name, language):
    proto_params = _PROTO_PARAMS_MAP[language]
    pkg_dir = os.path.join(output_dir, api_name + '-gen-' + language)
    subprocess.call(['mkdir', '-p', proto_params.code_root(pkg_dir)])
    return pkg_dir


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, src_proto_path, import_proto_path, output_dir,
                api_name):
        print 'Compiling descriptors {0}'.format(
            _find_protos(src_proto_path))
        desc_out_file = api_name + '.desc'
        subprocess.call(['mkdir', '-p', output_dir])
        subprocess.call(
            _protoc_header_params(import_proto_path, src_proto_path) +
            _protoc_desc_params(output_dir, desc_out_file) +
            _find_protos(src_proto_path))
        return os.path.join(output_dir, desc_out_file)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoCodeGenTask(task_base.TaskBase):
    """Generates protos"""
    def execute(self, language, src_proto_path, import_proto_path,
                output_dir, api_name):
        print 'Generating protos {0}'.format(
            _find_protos(src_proto_path))
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        subprocess.call(
            _protoc_header_params(import_proto_path, src_proto_path) +
            _protoc_proto_params(proto_params, pkg_dir) +
            _find_protos(src_proto_path))

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                gapi_tools_path, output_dir, api_name):
        print 'Running protoc with grpc plugin on {0}'.format(src_proto_path)
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        subprocess.call(
            _protoc_header_params(import_proto_path, src_proto_path) +
            _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path) +
            _find_protos(src_proto_path))

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoAndGrpcCodeGenTask(task_base.TaskBase):
    """Generates protos and the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                gapi_tools_path, output_dir, api_name):
        print 'Running protoc and grpc plugin on {0}'.format(src_proto_path)
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        subprocess.call(
            _protoc_header_params(import_proto_path, src_proto_path) +
            _protoc_proto_params(proto_params, pkg_dir) +
            _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path) +
            _find_protos(src_proto_path))

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class PackmanTask(task_base.TaskBase):
    """Checks packman requirements"""
    def execute(self, package_name, output_dir):
        subprocess.call(
            ['gen-api-package', '--api_name=' + package_name,
             '-l', 'python', '-o', output_dir])

    def validate(self):
        return [packman_requirements.PackmanRequirements]
