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
from taskflow.types import timing

from pipeline.utils import backend_helper


# TODO(cbao): This is now a common conductor which will execute all pipeline
# types. Turn this into an abstract class, and let its subclasses defines the
# pipelines types they can execute. Task requirements needed by pipelines shall
# be installed before conductor starts claiming jobs.
def run():
    # This continuously consumes until its stopped via ctrl-c or some other
    # kill signal...
    event_watches = {}

    # This will be triggered by the conductor doing various activities
    # with engines, and is quite nice to be able to see the various timing
    # segments (which is useful for debugging, or watching, or figuring out
    # where to optimize).
    def on_conductor_event(cond, event, details):
        print('Event \'%s\' has been received...' % event)
        print('Details = %s' % details)
        if event.endswith('_start'):
            w = timing.StopWatch()
            w.start()
            base_event = event[0:-len('_start')]
            event_watches[base_event] = w
        if event.endswith('_end'):
            base_event = event[0:-len('_end')]
            try:
                w = event_watches.pop(base_event)
                w.stop()
                print('It took %0.3f seconds for event \'%s\' to finish' %
                      (w.elapsed(), base_event))
            except KeyError:
                pass
        if event == 'running_end':
            cond.stop()

    conductor_id = os.getpid()
    print('Starting GAPIC conductor with pid: %s' % conductor_id)
    my_name = 'conductor-%s' % conductor_id
    persist_backend = backend_helper.default_persistence_backend()
    with contextlib.closing(persist_backend):
        with contextlib.closing(persist_backend.get_connection()) as conn:
            conn.upgrade()
        job_backend = backend_helper.default_jobboard_backend(my_name)
        job_backend.connect()
        with contextlib.closing(job_backend):
            cond = conductor_backends.fetch('blocking',
                                            my_name,
                                            job_backend,
                                            persistence=persist_backend)
            # on_conductor_event = functools.partial(on_conductor_event, cond)
            # cond.notifier.register(cond.notifier.ANY, on_conductor_event)
            # Run forever, and kill -9 or ctrl-c me...
            try:
                print('Conductor %s is running' % my_name)
                cond.run()
            finally:
                print('Conductor %s is stopping' % my_name)
                cond.stop()
                cond.wait()
