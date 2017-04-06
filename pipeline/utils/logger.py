# Copyright 2017 Google
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from colorlog import ColoredFormatter


logger = logging.getLogger('artman')
output_logger = logging.getLogger('artman.output')
output_logger.propagate = False


def setup_logging(level=logging.DEBUG):  # pragma: no cover
    logger.setLevel(level)
    output_logger.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()

    # Create a generalized formatter for all loggers.
    formatter = ColoredFormatter(
        "%(purple)s%(name)s > %(log_color)s%(message)s",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'blue',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Create a specialized logger for identifying output from
    # other processes.
    output_formatter = ColoredFormatter(
        "%(green)s%(name)s >\n%(log_color)s%(message)s",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    output_handler = logging.StreamHandler()
    output_handler.setFormatter(output_formatter)
    output_logger.addHandler(output_handler)

    # Silence noisy loggers
    logging.getLogger('sh').setLevel(logging.WARNING)
