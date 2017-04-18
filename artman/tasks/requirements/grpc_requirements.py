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

"""protoc requirements class."""

import subprocess

from artman.tasks.requirements import task_requirement_base


class GrpcRequirements(task_requirement_base.TaskRequirementBase):

    @classmethod
    def require(cls):
        """gRPC requires protoc and gRPC plugins.

        TODO(cbao): List more gRPC plugins.
        TODO(mukai): Take care of the installation of grpc_go_plugin.
        """
        return ['protoc', 'grpc_java_plugin', 'grpc_python_plugin',
                'grpc_go_plugin']

    @classmethod
    def install(cls):
        """Install protoc and gRPC plugins via a installation shell script."""
        curl_process = subprocess.Popen(
            ["curl", "-s", "http://goo.gl/getrpc"],
            stdout=subprocess.PIPE)
        bash_process = subprocess.Popen(
            ["bash", "-s", "--"],
            stdin=curl_process.stdout,
            stdout=subprocess.PIPE)
        curl_process.stdout.close()
        return bash_process.communicate()[0]
