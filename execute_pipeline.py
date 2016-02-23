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
                        pipeline_kwargs string, e.g. {'sleep_secs':3, 'id':1}

Example:

  python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':4} SamplePipeline

"""

import argparse
import ast
import os
import yaml

from taskflow import engines, task
from pipeline.pipelines import pipeline_factory
from pipeline.utils import job_util


def main():
  pipeline_name, pipeline_kwargs, remote_mode = _parse_args()
  pipeline = pipeline_factory.make_pipeline(pipeline_name, **pipeline_kwargs)

  if remote_mode:
    job_util.post_remote_pipeline_job(pipeline)
  else:
    # Hardcoded to execute the pipeline in serial engine, though not necessarily.
    engine = engines.load(pipeline.flow, engine="serial", store=pipeline.kwargs)
    engine.run()


def _CreateArgumentParser():
  parser = argparse.ArgumentParser()
  parser.add_argument("pipeline_name",
                      type=str,
                      help="The name of the pipeline to run")
  parser.add_argument(
      "--remote_mode",
      action="store_true",
      help="When specified, the pipeline will be executed remotely")
  parser.add_argument(
      "--pipeline_kwargs",
      type=str,
      default="{}",
      help=
      "pipeline_kwargs string, e.g. {\'sleep_secs\':3, \'type\':\'sample\'}")
  parser.add_argument(
      "--config",
      type=str,
      help="Comma-delimited list of the form "
          + "/path/to/config.yaml:config_section")
  parser.add_argument(
      "--reporoot",
      type=str,
      default="..",
      help="Root directory where the input, output, and tool repositories live")
  return parser


def _load_config_spec(config_spec, repl_vars):
  (config_path, config_sections) = config_spec.strip().split(':')
  config_sections = config_sections.split('|')
  data = {}
  with open(config_path) as config_file:
    all_config_data = yaml.load(config_file)
  for section in config_sections:
    data.update(all_config_data[section])

  repl_vars["THISDIR"] = os.path.dirname(config_path)
  _var_replace_config_data(data, repl_vars)
  del repl_vars["THISDIR"]
  return data


def _parse_args():
  parser = _CreateArgumentParser()
  flags = parser.parse_args()

  pipeline_args = {}
  repl_vars = {"REPOROOT": flags.reporoot}
  if flags.config:
    for config_spec in flags.config.split(','):
      config_args = _load_config_spec(config_spec, repl_vars)
      pipeline_args.update(config_args)

  cmd_args = ast.literal_eval(flags.pipeline_kwargs)
  pipeline_args.update(cmd_args)
  print "Final args:"
  for (k, v) in pipeline_args.iteritems():
    print " ", k, ":", v

  return (flags.pipeline_name,
          pipeline_args,
          flags.remote_mode)


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


if __name__ == "__main__":
  main()
