"""Util class for programming-language-specific things.
"""

import os
import os.path


class LanguageParams:
    def code_root(self, base_dir):
        return base_dir


class PythonParams(LanguageParams):
    pass


class JavaParams(LanguageParams):
    def code_root(self, base_dir):
        return os.path.join(base_dir, 'src', 'main', 'java')


class GoParams(LanguageParams):
    def code_root(self, base_dir):
        gopath = os.environ['GOPATH']
        assert os.path.realpath(base_dir).startswith(os.path.realpath(gopath))
        return base_dir

LANG_PARAMS_MAP = {
    'python': PythonParams(),
    'java': JavaParams(),
    'go': GoParams()
}
