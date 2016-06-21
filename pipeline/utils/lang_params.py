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

"""Util class for programming-language-specific things.
"""

import os
import os.path


class LanguageParams:
    def code_root(self, base_dir):
        return base_dir


class JavaParams(LanguageParams):
    def code_root(self, base_dir):
        return os.path.join(base_dir, 'src', 'main', 'java')


class PhpParams(LanguageParams):
    def code_root(self, base_dir):
        return os.path.join(base_dir, 'src')


LANG_PARAMS_MAP = {
    'python': LanguageParams(),
    'ruby': LanguageParams(),
    'nodejs': LanguageParams(),
    'java': JavaParams(),
    'go': LanguageParams(),
    'csharp': LanguageParams(),
    'php': PhpParams(),
}
