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

'''GAPIC conductor method.
'''

import contextlib
import os

from taskflow.conductors import backends as conductor_backends

from pipeline.utils import backend_helper


# TODO(cbao): This is now a common conductor which will execute all pipeline
# types. Turn this into an abstract class, and let its subclasses defines the
# pipelines types they can execute. Task requirements needed by pipelines shall
# be installed before conductor starts claiming jobs.
def run(jobboard_name):
    conductor_id = os.getpid()
    print('Starting GAPIC conductor with pid: %s' % conductor_id)
    my_name = 'conductor-%s' % conductor_id
    persist_backend = backend_helper.default_persistence_backend()
    with contextlib.closing(persist_backend):
        with contextlib.closing(persist_backend.get_connection()) as conn:
            conn.upgrade()
        jobboard = backend_helper.get_jobboard(my_name, jobboard_name)
        jobboard.connect()
        with contextlib.closing(jobboard):
            cond = conductor_backends.fetch('blocking',
                                            my_name,
                                            jobboard,
                                            persistence=persist_backend,
                                            engine='serial')
            # Run forever, and kill -9 or ctrl-c me...
            try:
                print('Conductor %s is running' % my_name)
                cond.run()
            finally:
                print('Conductor %s is stopping' % my_name)
                cond.stop()
                cond.wait()
