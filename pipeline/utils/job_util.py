"""Util class for job-related operations.
"""

import contextlib
import functools
import logging
import os
import sys
import time
import traceback

from taskflow.conductors import backends as conductor_backends
from taskflow import engines
from taskflow.jobs import backends as job_backends
from taskflow.patterns import linear_flow as lf
from taskflow.persistence import backends as persistence_backends
from taskflow.persistence import logbook
from taskflow import task
from taskflow.types import timing

from oslo_utils import uuidutils

from pipeline.pipelines import pipeline_factory
from pipeline.utils import backend_helper


def post_remote_pipeline_job(pipeline):
  ME = os.getpid()
  print("Starting poster with pid: %s" % ME)
  my_name = "poster-%s" % ME
  persist_backend = backend_helper.default_persistence_backend()
  with contextlib.closing(persist_backend):
    with contextlib.closing(persist_backend.get_connection()) as conn:
      conn.upgrade()
    job_backend = backend_helper.default_jobboard_backend(my_name)
    job_backend.connect()
    with contextlib.closing(job_backend):
      # Create information in the persistence backend about the
      # unit of work we want to complete and the factory that
      # can be called to create the tasks that the work unit needs
      # to be done.
      lb = logbook.LogBook("post-from-%s" % my_name)
      fd = logbook.FlowDetail("sample-from-%s" % my_name,
                              uuidutils.generate_uuid())
      lb.add(fd)
      with contextlib.closing(persist_backend.get_connection()) as conn:
        conn.save_logbook(lb)

      engines.save_factory_details(fd,
                                   pipeline_factory.make_pipeline_flow,
                                   [pipeline.name],
                                   pipeline.kwargs,
                                   backend=persist_backend)
      # Post, and be done with it!
      jb = job_backend.post("sample-job-from-%s" % my_name, book=lb)
      print("Posted: %s" % jb)
      return jb
