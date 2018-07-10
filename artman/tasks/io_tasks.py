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

"""Tasks related to I/O."""

import base64
import io
import os
import shutil
import zipfile

from six.moves import urllib

from gcloud import storage

from artman.tasks import task_base
from artman.utils.logger import logger


class PrepareGoogleapisDirTask(task_base.TaskBase):

    default_provides = ('remote_repo_dir')

    def execute(self, root_dir, files_dict={}):
        repo_root = os.path.abspath(os.path.join(root_dir, os.pardir))
        if os.path.exists(os.path.realpath(os.path.expanduser(repo_root))):
            # Do nothing if the repo_root exists. The repo_root exists if
            # artman is running locally.
            return
        logger.info('root repo: %s' % repo_root)
        try:
            os.makedirs(repo_root)
        except OSError as e:
            raise e
        testfile = urllib.request.FancyURLopener()
        tmp_repo_file = os.path.join(repo_root, "file.zip")
        testfile.retrieve(
            "https://github.com/googleapis/googleapis/archive/master.zip",
            tmp_repo_file)
        zip_ref = zipfile.ZipFile(tmp_repo_file, 'r')
        zip_ref.extractall(repo_root)
        zip_ref.close()
        os.remove(tmp_repo_file)
        shutil.move(os.path.join(repo_root, "googleapis-master"),
                    os.path.join(repo_root, "googleapis"))
        remote_repo_dir = os.path.join(repo_root, "googleapis")
        # Write/overwrite the additonal files into the remote_repo_dir so that
        # user can include additional files which are not in the public repo.
        for f, content in files_dict.items():
            filename = os.path.join(remote_repo_dir, f)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            with io.open(filename, "w+", encoding='UTF-8') as text_file:
                text_file.write(base64.b64decode(content))
        return remote_repo_dir


class PrepareOutputDirectoryTask(task_base.TaskBase):
    def execute(self, output_dir):
        self.exec_command(['mkdir', '-p', output_dir])
