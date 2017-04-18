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
"""Util class for job-related operations."""

from __future__ import print_function
import contextlib
import os
import time

from oslo_utils import uuidutils

from taskflow import engines
from taskflow import states
from taskflow.persistence import logbook

from artman.pipelines import pipeline_factory
from artman.utils import backend_helper
from artman.utils.logger import logger

# TODO(cbao): Include machine name
POSTER_NAME = "poster-%s" % os.getpid()


def post_remote_pipeline_job_and_wait(pipeline, jobboard_name):
    """Post a pipeline job and wait until it is finished."""
    my_name = POSTER_NAME
    logger.info("Starting poster with name: %s" % my_name)
    persist_backend = backend_helper.default_persistence_backend()
    with contextlib.closing(persist_backend):
        with contextlib.closing(persist_backend.get_connection()) as conn:
            conn.upgrade()
        jobboard = backend_helper.get_jobboard(my_name, jobboard_name)
        jobboard.connect()
        with contextlib.closing(jobboard):
            # Create information in the persistence backend about the
            # unit of work we want to complete and the factory that
            # can be called to create the tasks that the work unit needs
            # to be done.
            lb = logbook.LogBook("post-from-%s" % my_name)
            flow_uuid = uuidutils.generate_uuid()
            fd = logbook.FlowDetail("flow-of-%s" % my_name, flow_uuid)
            lb.add(fd)
            with contextlib.closing(persist_backend.get_connection()) as conn:
                conn.save_logbook(lb)

            engines.save_factory_details(fd,
                                         pipeline_factory.make_pipeline_flow,
                                         [pipeline.name, True],
                                         pipeline.kwargs,
                                         backend=persist_backend)
            # Post, and be done with it!
            jb = jobboard.post("job-from-%s" % my_name, book=lb)
            logger.info('Posted: %s' % jb)
            # TODO(cbao): Move wait until into a seperate method.
            # TODO(lukesneeringer): ...and fix the logging.
            state = states.UNCLAIMED
            print('Job status: %s' % state)
            while state != states.COMPLETE:
                if (jb.state != state):
                    state = jb.state
                    print('Job status: %s' % state)
                time.sleep(1)
            return jb


def fetch_job_status(jb, jobboard_name):
    result = []
    my_name = POSTER_NAME
    persist_backend = backend_helper.default_persistence_backend()
    with contextlib.closing(persist_backend):
        with contextlib.closing(persist_backend.get_connection()) as conn:
            conn.upgrade()
        jobboard = backend_helper.get_jobboard(my_name, jobboard_name)
        jobboard.connect()
        with contextlib.closing(jobboard):
            with contextlib.closing(persist_backend.get_connection()) as conn:
                for flow in jb.book:
                    flow_detail = conn.get_flow_details(flow.uuid)
                    result += flow_detail
    return result, flow_detail
