#!/usr/bin/env python

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

"""CLI to execute pipeline either locally or remotely.

Usage: execute_pipeline.py [-h] [--remote_mode]
                           [--pipeline_kwargs PIPELINE_KWARGS]
                           pipeline_name

positional arguments:
  pipeline_name         The name of the pipeline to run

optional arguments:
  -h, --help            show this help message and exit
  --remote_mode         When specified, the pipeline will be executed remotely
  --pipeline_kwargs PIPELINE_KWARGS
                        pipeline_kwargs string, e.g. "{'sleep_secs':3, 'id':1}"

Example:

  python execute_pipeline.py --pipeline_kwargs "{'sleep_secs':4}" SamplePipeline

"""

import argparse
import ast
import base64
import os
import tempfile
import time
import uuid
import yaml

from gcloud import storage
from gcloud import logging
from taskflow import engines, task, states
from pipeline.pipelines import pipeline_factory
from pipeline.utils import job_util, pipeline_util


def main():
  pipeline_name, pipeline_kwargs, env, local_repo = _parse_args()

  if local_repo:
    pipeline_kwargs = _load_local_repo(local_repo, **pipeline_kwargs)

  if env:
    # Execute pipeline task remotely based on the specified env param.
    pipeline = pipeline_factory.make_pipeline(
        pipeline_name, True, **pipeline_kwargs)
    jb = job_util.post_remote_pipeline_job_and_wait(pipeline, env)
    task_details, flow_detail = job_util.fetch_job_status(jb, env)

    for task_detail in task_details:
        if task_detail.name == 'BlobUploadTask' and task_detail.results:
            bucket_name, path, _ = task_detail.results
            pipeline_util.download_from_gcs(bucket_name, path,
                                            os.path.join(tempfile.gettempdir(),
                                            'artman-remote'))

    if flow_detail.state != 'SUCCESS':
      # Print the remote log if the pipeline execution completes but not with
      # SUCCESS status.
      _print_log(pipeline_kwargs['pipeline_id'])

  else:
    pipeline = pipeline_factory.make_pipeline(
        pipeline_name, False, **pipeline_kwargs)
    # Hardcoded to run pipeline in serial engine, though not necessarily.
    engine = engines.load(pipeline.flow, engine='serial', store=pipeline.kwargs)
    engine.run()


def _CreateArgumentParser():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      'pipeline_name',
      type=str,
      help='The name of the pipeline to run')
  parser.add_argument(
      '--pipeline_kwargs',
      type=str,
      default='{}',
      help=
      'pipeline_kwargs string, e.g. {\'sleep_secs\':3, \'type\':\'sample\'}')
  parser.add_argument(
      '--config',
      type=str,
      help='Comma-delimited list of the form '
          + '/path/to/config.yaml:config_section')
  parser.add_argument(
      '--reporoot',
      type=str,
      default='..',
      help='Root directory where the input, output, and tool repositories live')
  parser.add_argument(
      '--local_repo',
      type=str,
      default=None,
      help='Directory where local proto and gapic configs lives.')
  parser.add_argument(
        '--env',
        type=str,
        default=None,
        help='Environment for remote execution (valid value is \'remote\', and '
             'is case-insensitive. Pipeline will be executed locally if this '
             'flag is not provided.')
  return parser


def _load_config_spec(config_spec, repl_vars):
  (config_path, config_sections) = config_spec.strip().split(':')
  config_sections = config_sections.split('|')
  data = {}
  with open(config_path) as config_file:
    all_config_data = yaml.load(config_file)
  for section in config_sections:
    data.update(all_config_data[section])

  repl_vars['THISDIR'] = os.path.dirname(config_path)
  _var_replace_config_data(data, repl_vars)
  del repl_vars['THISDIR']
  return data


def _parse_args():
  parser = _CreateArgumentParser()
  flags = parser.parse_args()

  repo_root = flags.reporoot
  pipeline_args = {}

  if flags.env:
    pipeline_id = str(uuid.uuid4())
    # Use a unique randome temp directory for remote execution.
    # TODO(ethanbao): Let remote artman decide the temp directory.
    repo_root = '/tmp/artman/%s' % pipeline_id
    pipeline_args['pipeline_id'] = pipeline_id

  pipeline_args['repo_root'] = repo_root
  # TODO(ethanbao): Remove TOOLKIT_HOME var after toolkit_path is removed from
  # gapic yaml.
  repl_vars = {'REPOROOT': repo_root,
               'TOOLKIT_HOME': os.path.join(flags.reporoot, 'toolkit')}

  if flags.config:
    for config_spec in flags.config.split(','):
      config_args = _load_config_spec(config_spec, repl_vars)
      pipeline_args.update(config_args)

  cmd_args = ast.literal_eval(flags.pipeline_kwargs)
  pipeline_args.update(cmd_args)
  print 'Final args:'
  for (k, v) in pipeline_args.iteritems():
    print ' ', k, ':', v

  return (flags.pipeline_name,
          pipeline_args,
          flags.env.lower() if flags.env else None,
          flags.local_repo)


def _var_replace_config_data(data, repl_vars):
  for (k, v) in data.items():
    if type(v) is list:
      data[k] = [_var_replace(lv, repl_vars) for lv in v]
    elif type(v) is not bool:
      data[k] = _var_replace(v, repl_vars)


def _var_replace(in_str, repl_vars):
  new_str = in_str
  for (k, v) in repl_vars.iteritems():
    new_str = new_str.replace('${' + k + '}', v)
  return new_str


def _load_local_repo(private_repo_root, **pipeline_kwargs):
  files_dict = {}
  for root, dirs, files in os.walk(private_repo_root):
      for fname in files:
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, private_repo_root)
        with open(path, 'r') as f:
          files_dict[_normalize_path(rel_path)] = base64.b64encode(f.read())

  pipeline_kwargs['files_dict'] = files_dict
  return pipeline_kwargs

def _normalize_path(path):
    """Normalize the file path into one using slash as the seperator."""
    parts = []
    while True:
        head, tail = os.path.split(path)
        if head == path:
            assert not tail
            if path:
                parts.append(head)
            break
        parts.append(tail)
        path = head
    parts.reverse()
    return "/".join(parts)

def _print_log(pipeline_id):
  # Fetch the cloud logging entry if the exection fails. Wait for 30 secs,
  # because it takes a while for the logging to become available.
  print('The remote pipeline execution failed. It will wait for 30 secs before '
        'fetching the log for remote pipeline execution.')
  time.sleep(30)
  try:
      client = logging.Client()
      logger = client.logger(pipeline_id)
      entries, token = logger.list_entries()
      for entry in entries:
          print entry.payload
  except:
      pass

  print('You can always run the following command to fetch the log entry:\n'
        '    gcloud beta logging read "logName=projects/vkit-pipeline/logs/%s"' % pipeline_id)

if __name__ == "__main__":
  main()
