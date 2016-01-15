"""protoc requirement class."""

import subprocess

from task_requirement_base import TaskRequirementBase


class GrpcRequirement(TaskRequirementBase):

  @classmethod
  def require(cls):
    """Grpc requires protoc and grpc plugins.

    TODO(cbao): List more grpc plugins.
    """
    return ['protoc', 'grpc_java_plugin', 'grpc_python_plugin']

  @classmethod
  def install(cls):
    """Install protoc and grpc plugins via a installation shell script."""
    curl_process = subprocess.Popen(
        ["curl", "-s", "https://raw.githubusercontent.com/grpc/homebrew-grpc/master/scripts/install"],
        stdout=subprocess.PIPE)
    bash_process = subprocess.Popen(
        ["bash", "-s", "--"],
        stdin=curl_process.stdout,
        stdout=subprocess.PIPE)
    curl_process.stdout.close()
    return bash_process.communicate()[0]

