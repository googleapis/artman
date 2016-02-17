"""Tasks related to protoc"""

import os
import re
import subprocess
from pipeline.tasks import task_base
from pipeline.tasks.requirements import go_requirements
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

    def lang_out_param(self, output_dir, with_grpc):
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

    def lang_out_param(self, output_dir, with_grpc):
        return '--java_out=' + self.code_root(output_dir)

    def grpc_plugin_path(self, gapi_tools_path):
        if self.path is None:
            print 'start gradle process to locate GRPC Java plugin'
            self.path = task_utils.runGradleTask(
                'showGrpcJavaPluginPath', gapi_tools_path,
                'protoc-gen-grpc-java')
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)


class _GoProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['go']

    def code_root(self, output_dir):
        # Go protoc always generates from $GOPATH, otherwise the import
        # locations aren't generated correctly.
        return os.path.join(os.environ['GOPATH'], 'src')

    def lang_out_param(self, output_dir, with_grpc):
        param = '--go_out='
        if with_grpc:
            param += 'plugins=grpc:'
        return param + self.code_root(output_dir)

    def grpc_plugin_path(self, gapi_tools_path):
        # Go gRPC code is generated through --go_out=plugin=grpc, no grpc
        # specific plugin.
        return None

    def grpc_out_param(self, output_dir):
        # Go gRPC output directory is specified from --go_out, thus this
        # returns None.
        return None


_PROTO_PARAMS_MAP = {
    'python': _PythonProtoParams(),
    'java': _JavaProtoParams(),
    'go': _GoProtoParams()
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


def _group_by_dirname(protos):
    """Groups the file paths by direct parent directory.

    Returns:
        A dict mapping from the directory name to the list of proto files in
        it.
    """
    dirs = {}
    for proto in protos:
        dirname = os.path.dirname(proto)
        if dirname not in dirs:
            dirs[dirname] = [proto]
        else:
            dirs[dirname].append(proto)
    return dirs


def _protoc_header_params(import_proto_path, src_proto_path):
    return (['protoc'] +
            ['--proto_path=' + path for path in
             (import_proto_path + src_proto_path)])


def _protoc_desc_params(output_dir, desc_out_file):
    return (['--include_imports',
             '--include_source_info',
             '-o', os.path.join(output_dir, desc_out_file)])


def _protoc_proto_params(proto_params, pkg_dir, with_grpc):
    return [proto_params.lang_out_param(pkg_dir, with_grpc)]


def _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path):
    plugin_path = proto_params.grpc_plugin_path(gapi_tools_path)
    if plugin_path is None:
        return []
    return ['--plugin=protoc-gen-grpc=' + plugin_path,
            proto_params.grpc_out_param(pkg_dir)]


def _prepare_pkg_dir(output_dir, api_name, language):
    proto_params = _PROTO_PARAMS_MAP[language]
    pkg_dir = os.path.join(output_dir, api_name + '-gen-' + language)
    subprocess.call(['mkdir', '-p', proto_params.code_root(pkg_dir)])
    return pkg_dir


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, proto_path, import_proto_path, output_dir,
                api_name):
        print 'Compiling descriptors {0}'.format(
            _find_protos(proto_path))
        desc_out_file = api_name + '.desc'
        subprocess.call(['mkdir', '-p', output_dir])
        # DescGen don't use _group_by_dirname right now because
        #   - it doesn't have to
        #   - and multiple invocation will overwrite the desc_out_file
        subprocess.call(
            _protoc_header_params(import_proto_path, proto_path) +
            _protoc_desc_params(output_dir, desc_out_file) +
            _find_protos(proto_path))
        return os.path.join(output_dir, desc_out_file)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoCodeGenTask(task_base.TaskBase):
    """Generates protos"""
    def execute(self, language, proto_path, import_proto_path,
                output_dir, api_name):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # protoc-gen-go must compile all protos in a package at the same time,
        # and *only* the protos in that package. This doesn't break other
        # languages, so we do it that way for all of them.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(proto_path)).items():
            print 'Generating protos {0}'.format(dirname)
            subprocess.call(
                _protoc_header_params(import_proto_path, proto_path) +
                _protoc_proto_params(proto_params, pkg_dir, with_grpc=False) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, language, proto_path, import_proto_path,
                gapi_tools_path, output_dir, api_name):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # See the comments in ProtoCodeGenTask for why this needs to group the
        # proto files by directory.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(proto_path)).items():
            print 'Running protoc with grpc plugin on {0}'.format(dirname)
            subprocess.call(
                _protoc_header_params(import_proto_path, proto_path) +
                _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoAndGrpcCodeGenTask(task_base.TaskBase):
    """Generates protos and the gRPC client library"""
    def execute(self, language, proto_path, import_proto_path,
                gapi_tools_path, output_dir, api_name):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # See the comments in ProtoCodeGenTask for why this needs to group the
        # proto files by directory.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(proto_path)).items():
            print 'Running protoc and grpc plugin on {0}'.format(dirname)
            subprocess.call(
                _protoc_header_params(import_proto_path, proto_path) +
                _protoc_proto_params(proto_params, pkg_dir, with_grpc=True) +
                _protoc_grpc_params(proto_params, pkg_dir, gapi_tools_path) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoPathTask(task_base.TaskBase):
    """Creates the proto_path for further tasks. This simply reuses
    src_proto_path but subclass may prepare another directory and make some
    local edits."""
    default_provides = 'proto_path'

    def execute(self, src_proto_path):
        return src_proto_path


class GoLangUpdateProtoImportsTask(task_base.TaskBase):
    """Copies the proto files into the target directory under $GOPATH, and
    modifies import paths.

    The Go compiler requires source files to specify the import path as the
    relative path from $GOPATH/src, and therefore the import path in proto
    files have to be in the same format.

    Right now this task copies both core protos and service protos into the
    output directory (and tweaks their import declarations). This is because
    there is no repositories for the pb.go files and proto files outside of
    the project.

    Once the repository is created, core protos don't have to be processed
    here, the service protos will point to the repository for core protos.
    """
    default_provides = 'proto_path'

    def execute(self, src_proto_path, output_dir):
        """Copies proto files from the specified paths into the output
        directories and updates the imports to be relative to $GOPATH/src.

        Returns:
            The list of output directories.
        """
        output_dirs = set()
        output_base = os.path.join(output_dir, 'proto')
        import_base = self.get_import_base(output_dir)
        for dirname in src_proto_path:
            for proto in _find_protos([dirname]):
                output = os.path.join(
                        output_base, os.path.relpath(proto, dirname))
                output_dir = os.path.dirname(output)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_dirs.add(output_dir)
                with open(proto) as fin:
                    with open(output, 'w') as fout:
                        for line in fin:
                            fout.write(self.modify_imports(import_base, line))
        return list(output_dirs)

    def get_import_base(self, output_dir):
        gopathsrc = os.path.realpath(os.path.join(os.environ['GOPATH'], 'src'))
        import_base = os.path.join(
            os.path.realpath(output_dir)[len(gopathsrc)+1:], 'proto')
        if os.sep != '/':
            import_base = import_base.replace(os.sep, '/')
        return import_base

    def modify_imports(self, import_base, line):
        """Modifies the imports in a proto file relative to $GOPATH/src, so that
        generated pb.go files can point to the right location."""
        pattern = r'^import "google/'
        replacement = 'import "%s/google/' % import_base
        return re.sub(pattern, replacement, line)

    def validate(self):
        return [go_requirements.GoPathRequirements]


class GrpcPackmanTask(task_base.TaskBase):
    """Checks packman requirements"""
    def execute(self, api_name, output_dir):
        # Fix the api_name convention (ex. logging-v2) for packman.
        api_name = api_name.replace('-', '/')
        subprocess.call(
            ['gen-api-package', '--api_name=' + api_name,
             '-l', 'python', '-o', output_dir])

    def validate(self):
        return [packman_requirements.PackmanRequirements]
