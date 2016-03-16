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

"""Utils related to pipeline"""

import os
import subprocess
import urlparse


def validate_exists(required, **kwargs):
    for arg in required:
        if arg not in kwargs:
            raise ValueError('{0} must be provided'.format(arg))


def download(url, directory):
    filename = os.path.basename(urlparse.urlsplit(url).path)
    if not os.path.isfile(os.path.join(directory, filename)):
        subprocess.check_call(['mkdir', '-p', directory])
        print 'Downloading file from URL:' + url
        subprocess.check_call(
            ['curl', '-o', directory + filename, '-sL', url])
    return directory + filename
