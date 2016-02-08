"""One-line documentation for backend_helper module.

"""

from taskflow.jobs import backends as job_backends
from taskflow.persistence import backends as persistence_backends

# Default host/port of ZooKeeper service.
ZK_HOST = '104.197.10.180:2181'

# Default jobboard configuration.
JB_CONF = {
    'hosts': ZK_HOST,
    'board': 'zookeeper',
    'path': '/dev/jobs',
}

# Default persistence configuration.
PERSISTENCE_CONF = {
    'connection': 'zookeeper',
    'hosts': ZK_HOST,
    'path': '/taskflow/persistence',
}


def default_persistence_backend():
    return persistence_backends.fetch(PERSISTENCE_CONF)


def default_jobboard_backend(name):
    return job_backends.fetch(name,
                              JB_CONF,
                              persistence=default_persistence_backend())
