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

"""Batch pipelines"""

import glob
import six
import os

from artman.pipelines import code_generation as code_gen
from taskflow.patterns import linear_flow
from artman.utils import config_util
from artman.cli.support import select_git_repo


class BatchPipeline(code_gen.CodeGenerationPipelineBase):

    def __init__(self, make_pipeline_tasks_func, **kwargs):
        task_factory = BatchTaskFactory(make_pipeline_tasks_func)
        super(BatchPipeline, self).__init__(
            task_factory, **kwargs)


class BatchTaskFactory(code_gen.TaskFactoryBase):

    def __init__(self, make_pipeline_tasks_func):
        self.make_pipeline_tasks_func = make_pipeline_tasks_func
        super(BatchTaskFactory, self).__init__()

    def get_tasks(self, **kwargs):
        batch_flow = linear_flow.Flow('BatchFlow')
        for single_flow in self.get_language_api_flows(**kwargs):
            batch_flow.add(single_flow)
        return [batch_flow]

    def get_language_api_flows(self, batch_apis, language,
                               api_config_patterns, artman_language_yaml,
                               local_paths, **kwargs):

        artman_config_yamls = _get_artman_config_filenames(
            api_config_patterns, batch_apis)

        for api_kwargs in _get_api_kwarg_dicts(
                artman_config_yamls,
                language,
                artman_language_yaml,
                local_paths):

            api_kwargs.update(kwargs)

            # Coerce `git_repos` and `target_repo` into a single git_repo.
            if api_kwargs['publish'] in ('github', 'local'):
                # Pop the git repos off of the pipeline args and select the
                # correct one.
                repos = api_kwargs.pop('git_repos')
                api_kwargs['git_repo'] = select_git_repo(repos, None)

            yield self.make_single_language_flow(**api_kwargs)

    def make_single_language_flow(self, **kwargs):
        single_flow = linear_flow.Flow('SingleLanguageApiFlow')
        tasks = self.make_pipeline_tasks_func(**kwargs)
        single_flow.add(*tasks)
        return single_flow

    def get_validate_kwargs(self, **kwargs):
        return ['batch_apis', 'language', 'api_config_patterns',
                'artman_language_yaml', 'publish']

    def get_invalid_kwargs(self):
        return []


def _get_api_kwarg_dicts(
        artman_config_yamls, language, artman_language_yaml, local_paths):
    lang_config = _load_artman_config(artman_language_yaml,
                                      language,
                                      local_paths)
    lang_config['language'] = language
    for api_config_yaml in artman_config_yamls:
        api_config = _load_artman_config(api_config_yaml,
                                         language,
                                         local_paths)
        if not api_config.get('enable_batch_generation', True):
            continue
        api_kwargs = lang_config.copy()
        api_kwargs.update(api_config)
        yield api_kwargs


def _get_artman_config_filenames(api_config_patterns, batch_apis):
    # We consider two separate cases: when batch_apis='*', and when batch_apis
    # is a list. In the first case, we find all files which match the patterns
    # listed in api_config_patterns. In the second case, for each api listed in
    # batch_apis, we try to find a matching file in EXACTLY ONE of the
    # api_config_patterns.
    config_filenames= []
    if batch_apis == '*':
        for pattern in api_config_patterns:
            glob_pattern = config_util.replace_vars(pattern,
                                                   {'API_SHORT_NAME': '*'})
            config_filenames += sorted(glob.glob(glob_pattern))
    else:
        if isinstance(batch_apis, (six.text_type, six.binary_type)):
            batch_apis = batch_apis.split(',')
        for api in batch_apis:
            api_filenames = []
            for pattern in api_config_patterns:
                api_filename = config_util.replace_vars(pattern,
                                                        {'API_SHORT_NAME': api})
                if os.path.isfile(api_filename):
                    api_filenames.append(api_filename)
            if len(api_filenames) > 1:
                raise ValueError('Multiple candidate artman yamls for api '
                                 '%s: %s' % api, api_filenames)
            if len(api_filenames) == 0:
                raise ValueError('No artman yamls found for api %s' % api)
            config_filenames += api_filenames
    return config_filenames


def _load_artman_config(artman_yaml, language, local_paths):
    return config_util.load_config_spec(
        config_spec=artman_yaml,
        config_sections=['common'],
        repl_vars={k.upper(): v for k, v in local_paths.items()},
        language=language)
