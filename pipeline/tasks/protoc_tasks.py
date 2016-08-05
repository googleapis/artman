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

"""Tasks related to protoc"""

import os
import re
import subprocess
from pipeline.tasks import packman_tasks
from pipeline.tasks import task_base
from pipeline.tasks.requirements import grpc_requirements
from pipeline.utils import lang_params
from pipeline.utils import task_utils


class _SimpleProtoParams:
    def __init__(self, language):
        self.language = language
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP[language]

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--{}_out={}'.format(self.language, self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'grpc_{}_plugin'.format(self.language)])[:-1]
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

    def grpc_plugin_path(self, toolkit_path):
        if self.path is None:
            print 'start gradle process to locate GRPC Java plugin'
            self.path = task_utils.run_gradle_task(
                'showGrpcJavaPluginPath', toolkit_path)
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)


class _GoProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['go']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        param = '--go_out='
        if with_grpc:
            param += 'plugins=grpc:'
        return param + self.code_root(output_dir)

    def grpc_plugin_path(self, toolkit_path):
        # Go gRPC code is generated through --go_out=plugin=grpc, no grpc
        # specific plugin.
        return None

    def grpc_out_param(self, output_dir):
        # Go gRPC output directory is specified from --go_out, thus this
        # returns None.
        return None


class _PhpProtoParams:
    def __init__(self):
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP['php']

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--php_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'protoc-gen-php'], stderr=subprocess.STDOUT)[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)


_PROTO_PARAMS_MAP = {
    'python': _SimpleProtoParams('python'),
    'ruby': _SimpleProtoParams('ruby'),
    'java': _JavaProtoParams(),
    'go': _GoProtoParams(),
    'csharp': _SimpleProtoParams('csharp'),
    'php': _PhpProtoParams(),
}


def _find_protobuf_path(toolkit_path):
    """Fetch and locate protobuf source"""
    print 'Searching for latest protobuf source'
    return task_utils.run_gradle_task(
        'showProtobufPath', toolkit_path)


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


def _protoc_header_params(import_proto_path, src_proto_path,
                          toolkit_path):
    proto_path = import_proto_path + src_proto_path
    proto_path.append(_find_protobuf_path(toolkit_path))
    return (['protoc'] +
            ['--proto_path=' + path for path in proto_path])


def _protoc_desc_params(output_dir, desc_out_file):
    return (['--include_imports',
             '--include_source_info',
             '-o', os.path.join(output_dir, desc_out_file)])


def _protoc_proto_params(proto_params, pkg_dir, with_grpc):
    return [proto_params.lang_out_param(pkg_dir, with_grpc)]


def _protoc_grpc_params(proto_params, pkg_dir, toolkit_path):
    plugin_path = proto_params.grpc_plugin_path(toolkit_path)
    if plugin_path is None:
        return []
    return ['--plugin=protoc-gen-grpc=' + plugin_path,
            proto_params.grpc_out_param(pkg_dir)]


def _prepare_pkg_dir(output_dir, api_name, language):
    proto_params = _PROTO_PARAMS_MAP[language]
    pkg_dir = os.path.join(output_dir, api_name + '-gen-' + language)
    subprocess.check_output([
        'mkdir', '-p', proto_params.code_root(pkg_dir)],
        stderr=subprocess.STDOUT)
    return pkg_dir


class ProtoDescGenTask(task_base.TaskBase):
    """Generates proto descriptor set"""
    default_provides = 'descriptor_set'

    def execute(self, src_proto_path, import_proto_path, output_dir,
                api_name, toolkit_path):
        print 'Compiling descriptors {0}'.format(
            _find_protos(src_proto_path))
        desc_out_file = api_name + '.desc'
        self.exec_command(['mkdir', '-p', output_dir])
        # DescGen don't use _group_by_dirname right now because
        #   - it doesn't have to
        #   - and multiple invocation will overwrite the desc_out_file
        self.exec_command(
            _protoc_header_params(
                import_proto_path, src_proto_path, toolkit_path) +
            _protoc_desc_params(output_dir, desc_out_file) +
            _find_protos(src_proto_path))
        return os.path.join(output_dir, desc_out_file)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoCodeGenTask(task_base.TaskBase):
    """Generates protos"""
    def execute(self, language, src_proto_path, import_proto_path,
                output_dir, api_name, toolkit_path):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # protoc-gen-go must compile all protos in a package at the same time,
        # and *only* the protos in that package. This doesn't break other
        # languages, so we do it that way for all of them.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(src_proto_path)).items():
            print 'Generating protos {0}'.format(dirname)
            self.exec_command(
                _protoc_header_params(
                    import_proto_path, src_proto_path, toolkit_path) +
                _protoc_proto_params(proto_params, pkg_dir, with_grpc=False) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GrpcCodeGenTask(task_base.TaskBase):
    """Generates the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # See the comments in ProtoCodeGenTask for why this needs to group the
        # proto files by directory.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(src_proto_path)).items():
            print 'Running protoc with grpc plugin on {0}'.format(dirname)
            self.exec_command(
                _protoc_header_params(
                    import_proto_path, src_proto_path, toolkit_path) +
                _protoc_grpc_params(proto_params, pkg_dir, toolkit_path) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class ProtoAndGrpcCodeGenTask(task_base.TaskBase):
    """Generates protos and the gRPC client library"""
    def execute(self, language, src_proto_path, import_proto_path,
                toolkit_path, output_dir, api_name):
        proto_params = _PROTO_PARAMS_MAP[language]
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        # See the comments in ProtoCodeGenTask for why this needs to group the
        # proto files by directory.
        for (dirname, protos) in _group_by_dirname(
                _find_protos(src_proto_path)).items():
            print 'Running protoc and grpc plugin on {0}'.format(dirname)
            self.exec_command(
                _protoc_header_params(
                    import_proto_path, src_proto_path, toolkit_path) +
                _protoc_proto_params(proto_params, pkg_dir, with_grpc=True) +
                _protoc_grpc_params(proto_params, pkg_dir, toolkit_path) +
                protos)

    def validate(self):
        return [grpc_requirements.GrpcRequirements]


class GoLangUpdateImportsTask(task_base.TaskBase):
    """Modifies the import in the generated pb.go files and copies them into
    the final_repo_dir.

    The Go compiler requires source files to specify the import path as the
    relative path from $GOPATH/src, however the import paths to other proto
    packages in the generated pb.go files don't fullfill this requirement. This
    task finds such import lines and rewrites them in the form of the original
    code.
    """

    def execute(self, api_name, language, go_import_base, output_dir,
                final_repo_dir):
        pkg_dir = _prepare_pkg_dir(output_dir, api_name, language)
        for pbfile in self.find_pb_files(pkg_dir):
            out_file = os.path.join(final_repo_dir, 'proto',
                                    os.path.relpath(pbfile, pkg_dir))
            out_dir = os.path.dirname(out_file)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            with open(pbfile) as fin:
                with open(out_file, 'w') as fout:
                    for line in fin:
                        fout.write(self.modify_imports(go_import_base, line))

    def find_pb_files(self, dirname):
        for root, _, files in os.walk(dirname):
            for filename in files:
                # os.path.splitext splits "foo.pb.go" to ("foo.pb", "go").
                (base, ext) = os.path.splitext(filename)
                if ext == '.go' and os.path.splitext(base)[1] == '.pb':
                    yield os.path.join(root, filename)

    def modify_imports(self, go_import_base, line):
        """Modifies incorrect imports in a pb.go file to point the correct
        files."""
        pattern = r'^import ([a-zA-Z0-9_]* )?"google/'
        replacement = 'import \g<1>"%s/proto/google/' % go_import_base
        return re.sub(pattern, replacement, line)


class GrpcPackmanTask(packman_tasks.PackmanTaskBase):
    def execute(self, language, api_name, output_dir, src_proto_path,
                import_proto_path, packman_flags=None, repo_dir=None):
        packman_flags = packman_flags or []
        api_name = task_utils.packman_api_name(api_name)
        arg_list = [language, api_name, '-o', output_dir,
                    '--package_prefix', 'google-']

        # Import path must be absolute. See
        #   https://github.com/googleapis/packman/issues/1
        import_proto_path = [os.path.abspath(imp) for imp in import_proto_path]

        arg_list += [arg for imp in import_proto_path for arg in ('-i', imp)]
        arg_list += [arg for src in src_proto_path for arg in ('-r', src)]
        arg_list += packman_flags
        if repo_dir:
            arg_list += ['-r', repo_dir]
        self.run_packman(*arg_list)
