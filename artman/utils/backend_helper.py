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

"""One-line documentation for backend_helper module.

"""

from taskflow.jobs import backends as job_backends
from taskflow.persistence import backends as persistence_backends

# Default host/port of ZooKeeper service.
ZK_HOST = '104.197.10.180:2181'

# Default persistence configuration.
PERSISTENCE_CONF = {
    'connection': 'zookeeper',
    'hosts': ZK_HOST,
    'path': '/taskflow/persistence',
}


def default_persistence_backend():
    return persistence_backends.fetch(PERSISTENCE_CONF)


def get_jobboard(name, jobboard_name):
    config = {
        'hosts': ZK_HOST,
        'board': 'zookeeper',
        'path': '/taskflow/jobboard/zookeeper/' + jobboard_name,
    }
    return job_backends.fetch(name, config,
                              persistence=default_persistence_backend())
