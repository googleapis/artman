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

"""Util class for job-related operations.
"""

import contextlib
import os

from taskflow import engines
from taskflow.persistence import logbook

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
