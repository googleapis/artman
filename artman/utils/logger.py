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

__all__ = ('logger', 'output_logger', 'setup_logging')


OUTPUT = 22
SUCCESS = 25

COLORS = {
    'DEBUG': 'blue',
    'INFO': 'cyan',
    'OUTPUT': 'white',
    'SUCCESS': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bold',
}


class Logger(logging.getLoggerClass()):
    def __init__(self, name, level=logging.NOTSET):
        super(Logger, self).__init__(name, level)
        logging.addLevelName(OUTPUT, 'OUTPUT')
        logging.addLevelName(SUCCESS, 'SUCCESS')

    def output(self, message, *args, **kwargs):
        if self.isEnabledFor(OUTPUT):
            self._log(OUTPUT, message, args, **kwargs)

    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, message, args, **kwargs)


logging.setLoggerClass(Logger)


def setup_logging(level=logging.DEBUG):  # pragma: no cover
    setup_logger(None, level)
    setup_logger('artman.output', level + 5,
        colors=dict(COLORS, OUTPUT='green'),
        format_string="%(log_color)s%(name)s >\n%(white)s%(message)s",
    )
    setup_logger('github3', level + 10, colors=dict(COLORS, INFO='blue'))
    setup_logger('sh', logging.WARNING)


def setup_logger(name, level, colors=COLORS,
                 format_string="%(purple)s%(name)s> %(log_color)s%(message)s"):
    """Set up a particular logger with overridden behavior.

    Args:
        name (str): The name of the logger.
        level (int): The log level to set this logger to.
        colors (dict): A dictionary of log colors.
        format_string (str): The format of the log message.
    """
    logger_ = logging.getLogger(name)
    logger_.setLevel(level)
    formatter = ColoredFormatter(format_string, reset=True, log_colors=colors)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger_.addHandler(handler)
    logger_.propagate = False
    return logger_


# Make the logger and output_logger available for import from elsewhere.
logger = logging.getLogger('artman')
output_logger = logging.getLogger('artman.output')
