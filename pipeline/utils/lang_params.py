"""Util class for programming-language-specific things.
"""

import os


class LanguageParams:
    def code_root(self, base_dir):
        return base_dir


class PythonParams(LanguageParams):
    pass


class JavaParams(LanguageParams):
    def code_root(self, base_dir):
        return os.path.join(base_dir, 'src', 'main', 'java')


LANG_PARAMS_MAP = {
    'python': PythonParams(),
    'java': JavaParams()
}
