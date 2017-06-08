# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Utilities for protoc tasks"""

import collections
import os
import re
import subprocess
import types
import sys

import six

from artman.utils import lang_params
from artman.utils import task_utils
from artman.utils.logger import logger


class _SimpleProtoParams(object):
    def __init__(self, language):
        self.language = language
        self.path = None
        self.params = lang_params.LANG_PARAMS_MAP[language]

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def proto_plugin_path(self, plugin_args=None):
        return None

    def plugin_out_param(self, output_dir, plugin_args=None):
        return None

    def lang_out_param(self, output_dir, with_grpc):
        return '--{}_out={}'.format(self.language, self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'grpc_{}_plugin'.format(self.language)],
                stderr=subprocess.STDOUT).decode('utf-8')
            self.path = six.text_type(self.path)[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _JavaProtoParams(_SimpleProtoParams):
    def __init__(self):
        super(_JavaProtoParams, self).__init__('java')

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def proto_plugin_path(self):
        return subprocess.check_output(
            ['which', 'gapic_plugin.py'],
            stderr=subprocess.STDOUT).strip().decode('utf-8')

    def plugin_out_param(self, output_dir, plugin_args=None):
        # Java proto plugin requires the gapic yaml as a plugin arg
        if plugin_args:
            return '--plgn_out={}:{}'.format(plugin_args,
                                             self.code_root(output_dir))
        else:
            return None

    def grpc_plugin_path(self, toolkit_path):
        if self.path is None:
            logger.info('start gradle process to locate GRPC Java plugin')
            self.path = task_utils.get_gradle_task_output(
                'showGrpcJavaPluginPath', toolkit_path)
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _GoProtoParams(_SimpleProtoParams):
    def __init__(self):
        super(_GoProtoParams, self).__init__('go')

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

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _PhpProtoParams(_SimpleProtoParams):
    def __init__(self):
        super(_PhpProtoParams, self).__init__('php')

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--php_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        if self.path is None:
            self.path = subprocess.check_output(
                ['which', 'protoc-gen-php'], stderr=subprocess.STDOUT)
            self.path = six.text_type(self.path)[:-1]
        return self.path

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['protoc']


class _RubyProtoParams(_SimpleProtoParams):
    def __init__(self):
        super(_RubyProtoParams, self).__init__('ruby')

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--ruby_out={}'.format(self.code_root(output_dir))

    def grpc_plugin_path(self, dummy_toolkit_path):
        # No plugin for grpc_toos_ruby_protoc
        return None

    def grpc_out_param(self, output_dir):
        return '--grpc_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return ['grpc_tools_ruby_protoc']


class _PythonProtoParams(_SimpleProtoParams):
    def __init__(self):
        super(_PythonProtoParams, self).__init__('python')

    def code_root(self, output_dir):
        return self.params.code_root(output_dir)

    def lang_out_param(self, output_dir, with_grpc):
        return '--python_out={root} --pydocstring_out={root}'.format(
            root=self.code_root(output_dir),
        )

    def grpc_plugin_path(self, dummy_toolkit_path):
        # No plugin for grpc.tools
        return None

    def grpc_out_param(self, output_dir):
        return '--grpc_python_out=' + self.code_root(output_dir)

    @property
    def proto_compiler_command(self):
        return [sys.executable, '-m', 'grpc.tools.protoc']


PROTO_PARAMS_MAP = {
    'ruby': _RubyProtoParams(),
    'java': _JavaProtoParams(),
    'go': _GoProtoParams(),
    'csharp': _SimpleProtoParams('csharp'),
    'php': _PhpProtoParams(),
    'python': _PythonProtoParams()
}


def group_by_dirname(protos):
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


def protoc_header_params(proto_path,
                          toolkit_path):
    proto_path = proto_path[:]
    proto_path.append(_find_protobuf_path(toolkit_path))
    return (['--proto_path=' + path for path in proto_path])


def protoc_desc_params(output_dir, desc_out_file):
    return (['--include_imports',
             '--include_source_info',
             '-o', os.path.join(output_dir, desc_out_file)])


def protoc_proto_params(proto_params, pkg_dir, gapic_api_yaml, with_grpc):
    params = []
    lang_param = proto_params.lang_out_param(pkg_dir, with_grpc)
    if lang_param:
        params += lang_param.split(' ')
    # plugin out must come after lang out
    plugin_param = proto_params.proto_plugin_path()
    plugin_out = proto_params.plugin_out_param(pkg_dir, gapic_api_yaml)
    if plugin_param and plugin_out:
        params.append('--plugin=protoc-gen-plgn={}'.format(plugin_param))
        params.append(plugin_out)
    return params


def protoc_grpc_params(proto_params, pkg_dir, toolkit_path):
    params = []
    plugin_param = proto_params.grpc_plugin_path(toolkit_path)
    if plugin_param:
        params.append('--plugin=protoc-gen-grpc={}'.format(plugin_param))
    grpc_param = proto_params.grpc_out_param(pkg_dir)
    if grpc_param:
        params.append(grpc_param)
    return params


def find_google_dir_index(src_proto_path):
    matches = list(re.finditer('(?:\\A|[/\\\\])(google)(?=\\Z|[/\\\\])',
                               src_proto_path))
    if len(matches) == 0:
        raise ValueError('src_proto_path did not contain "google" '
                         'in path as expected. src_proto_path: '
                         '"{}"'.format(src_proto_path))
    return matches[-1].start(1)


def pkg_root_dir(output_dir, api_name, api_version, organization_name,
                 language, prefix=None):
    pkg_name = task_utils.api_full_name(
        api_name, api_version, organization_name)
    if prefix is not None:
        pkg_name = prefix + pkg_name
    return os.path.join(output_dir, language, pkg_name)


def prepare_proto_pkg_dir(output_dir, api_name, api_version, organization_name,
                          language):
    return prepare_pkg_dir(output_dir, api_name, api_version, organization_name,
                            language, "proto-")


def prepare_grpc_pkg_dir(output_dir, api_name, api_version, organization_name,
                         language):
    return prepare_pkg_dir(output_dir, api_name, api_version, organization_name,
                            language, "grpc-")


def prepare_pkg_dir(output_dir, api_name, api_version, organization_name,
                    language, prefix):
    proto_params = PROTO_PARAMS_MAP[language]
    pkg_dir = pkg_root_dir(
        output_dir, api_name, api_version, organization_name, language, prefix)
    subprocess.check_output([
        'mkdir', '-p', proto_params.code_root(pkg_dir)],
        stderr=subprocess.STDOUT)
    return pkg_dir


def find_protos(proto_paths, excluded_proto_path):
    """Searches along `proto_paths` for .proto files and returns a generator of
    paths"""
    if not isinstance(proto_paths, (types.GeneratorType, collections.MutableSequence)):
        raise ValueError("proto_paths must be a list")
    for path in proto_paths:
        for root, _, files in os.walk(path):
            for proto in files:
                is_excluded = _is_proto_excluded(os.path.join(root, proto),
                                                 excluded_proto_path)
                if os.path.splitext(proto)[1] == '.proto' and not is_excluded:
                    yield os.path.join(root, proto)


def _is_proto_excluded(proto, excluded_proto_path):
    for excluded_path in excluded_proto_path:
        if excluded_path in proto:
            return True
    return False

_protobuf_path = None
def _find_protobuf_path(toolkit_path):
    """Fetch and locate protobuf source"""
    global _protobuf_path
    if not _protobuf_path:
        logger.info('Searching for latest protobuf source')
        _protobuf_path = task_utils.get_gradle_task_output(
            'showProtobufPath', toolkit_path)
    return _protobuf_path
