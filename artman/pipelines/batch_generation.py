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

"""Pipelines that run GAPIC"""

from ruamel import yaml
import glob

from artman.pipelines import code_generation as code_gen
from taskflow.patterns import linear_flow
from artman.utils import config_util, task_utils


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
        # TODO(michaelbausor): convert to unordered flow if necessary
        batch_flow = linear_flow.Flow('BatchFlow')
        for single_flow in self.get_language_api_flows(**kwargs):
            batch_flow.add(single_flow)

        # TODO(michaelbausor): add task to create Github PR once staging repo
        # is public on Github
        final_tasks = []

        flow = [batch_flow]
        flow += task_utils.instantiate_tasks(final_tasks, kwargs)

        return flow

    def get_language_api_flows(self, batch_apis, batch_languages,
                               api_config_pattern, artman_language_yaml,
                               **kwargs):

        repo_root = kwargs['repo_root']
        artman_config_yamls = _get_artman_config_filenames(
            api_config_pattern, batch_apis)

        for api_kwargs in _get_api_kwarg_dicts(
                artman_config_yamls,
                batch_languages,
                artman_language_yaml,
                repo_root):

            api_kwargs.update(kwargs)

            tasks = self.make_pipeline_tasks_func(**api_kwargs)

            single_flow = linear_flow.Flow('SingleLanguageApiFlow')
            single_flow.add(*tasks)
            yield single_flow

    def get_validate_kwargs(self, **kwargs):
        return ['batch_apis', 'batch_languages', 'api_config_pattern',
                'artman_language_yaml', 'publish']

    def get_invalid_kwargs(self, **kwargs):
        return ['language']


def _get_api_kwarg_dicts(
        artman_config_yamls, batch_languages, artman_language_yaml, repo_root):
    for language in _get_languages(artman_language_yaml, batch_languages):
        lang_config = _load_artman_config(artman_language_yaml,
                                          language,
                                          repo_root)
        # TODO(michaelbausor): change default to True once most API and
        # language combinations are supported
        if not lang_config.get('enable_batch_generation', False):
            continue
        for api_config_yaml in artman_config_yamls:
            api_config = _load_artman_config(api_config_yaml,
                                             language,
                                             repo_root)
            # TODO(michaelbausor): change default to True once most API and
            # language combinations are supported
            if not api_config.get('enable_batch_generation', False):
                continue
            api_kwargs = lang_config.copy()
            api_kwargs.update(api_config)
            api_kwargs['language'] = language
            yield api_kwargs


def _get_languages(artman_language_yaml, batch_languages):
    if batch_languages == '*':
        with open(artman_language_yaml) as config_file:
            batch_languages = sorted(yaml.load(config_file).keys())
        if 'common' in batch_languages:
            batch_languages.remove('common')
        return batch_languages
    else:
        return batch_languages.split(',')


def _get_artman_config_filenames(api_config_pattern, batch_apis):
    if batch_apis == '*':
        glob_pattern = config_util.var_replace(api_config_pattern,
                                               {'API_SHORT_NAME': '*'})
        return sorted(glob.glob(glob_pattern))
    else:
        return [config_util.var_replace(api_config_pattern,
                                        {'API_SHORT_NAME': api})
                for api in batch_apis.split(',')]


def _load_artman_config(artman_yaml, language, repo_root):
    sections = ['common']
    repl_vars = {'REPOROOT': repo_root}
    return config_util.load_config_spec(
        artman_yaml, sections, repl_vars, language)
