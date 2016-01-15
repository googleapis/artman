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

from taskflow import engines, task
from pipeline.pipelines import pipeline_factory
from pipeline.utils import job_util


def main():
  pipeline_name, pipeline_kwargs, remote_mode = _ParseArgs()
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
      help=
      "pipeline_kwargs string, e.g. {\'sleep_secs\':3, \'type\':\'sample\'}")
  # TODO(cbao): Support passing the pipeline kwargs via a config file.
  return parser


def _ParseArgs():
  parser = _CreateArgumentParser()
  flags = parser.parse_args()
  return (flags.pipeline_name,
          ast.literal_eval(flags.pipeline_kwargs),
          flags.remote_mode)


if __name__ == "__main__":
  main()
