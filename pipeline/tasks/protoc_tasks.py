"""Tasks related to protoc"""

import collections
import os
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements
from pipeline.tasks.requirements import packman_requirements


class _GrpcPythonPlugin:
    def __init__(self):
        self.path = None

    def output_parameter(self):
        return 'python_out'

    def plugin_path(self):
        if self.path is None:
            self.path = subprocess.check_output(['which', 'grpc_python_plugin'])[:-1]
        return self.path


class _GrpcJavaPlugin:
    def __init__(self):
        self.path = None

    def output_parameter(self):
        return 'java_out'

    def plugin_path(self):
        if self.path is None:
            self.path = subprocess.check_output(['which', 'protoc-gen-grpc-java'])[:-1]
        return self.path

_GRPC_PLUGIN_MAP = {
    'python': _GrpcPythonPlugin(),
    'java': _GrpcJavaPlugin()}

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


class ProtoDescriptorGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, service_proto_path, import_proto_path, output_dir):
        print 'Compiling descriptors {0}'.format(
            _find_protos(service_proto_path))
        out_file = 'descriptor.desc'
        subprocess.call(['mkdir', '-p', output_dir])
        subprocess.call(['protoc', '--include_imports'] +
                        ['--proto_path=' + path for path in
                         (service_proto_path + import_proto_path)] +
                        ['--include_source_info',
                         '-o', os.path.join(output_dir, out_file)] +
                        _find_protos(service_proto_path))
        return os.path.join(output_dir, out_file)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, language, service_proto_path, import_proto_path,
                output_dir):
        grpc_plugin = _GRPC_PLUGIN_MAP[language]
        for proto in _find_protos(service_proto_path):
            subprocess.call(
                ['protoc'] +
                ['--proto_path=' + path
                 for path in (import_proto_path + service_proto_path)] +
                ['--{0}='.format(grpc_plugin.output_parameter()) +
                 output_dir,
                 '--plugin=protoc-gen-grpc=' + grpc_plugin.plugin_path(),
                 '--grpc_out=' + output_dir, proto])
            print 'Running protoc on {0}'.format(proto)

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
