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

import uuid
from multiprocessing import Process
import unittest

from pipeline.pipelines import pipeline_factory
from pipeline.utils import job_util
from pipeline.conductors import gapic_conductor


class ConductorE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # global jobboard name for testing.
        cls.test_jobboard_name = 'test_jb_%s' % str(uuid.uuid4())
        cls.p = Process(
            target=_start_conductor, args=(cls.test_jobboard_name,))
        cls.p.start()

    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()

    def test_remote_sample_pipeline(self):
        pipeline_kwargs = {'sleep_secs': 1}
        pipeline = pipeline_factory.make_pipeline(
            'SamplePipeline', True, **pipeline_kwargs)
        jb = job_util.post_remote_pipeline_job_and_wait(
            pipeline, self.test_jobboard_name)
        task_details, flow_detail = job_util.fetch_job_status(
            jb, self.test_jobboard_name)
        self.assertEqual('SUCCESS', flow_detail.state)


def _start_conductor(test_jobboard_name):
    gapic_conductor.run(test_jobboard_name)
