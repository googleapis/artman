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

"""Base class for task requirement.

Each task requirement represents a tool chain requirement, which is needed by
one or more tasks. This will be used when conductor starts, or when some
requirements need to be installed before pipeline runs locally. One task might
require multiple requirements, and each requirement might also be needed by
different tasks."""

import subprocess


class TaskRequirementBase(object):

    @classmethod
    def require(cls):
        """Abstract method, which returns the list of required files or
        executables.

        Subclass must implment this method.

        """
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def install(cls):
        """Abstract method, which installs all required bits this tasks will
        need.

        Subclass must implment this method.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def is_installed(cls):
        """Return True if all requirements have been installed."""
        for exe in cls.require():
            # TODO(cbao): Use shutil.which() if running with Python 3.3 and
            # above.
            return_code = subprocess.call(["which", exe])
            if return_code:
                return False
        return True
