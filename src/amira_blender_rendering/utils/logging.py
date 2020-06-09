#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# logging setup

import os
import logging

# local logger configuration
__logger_name = "amira_blender_rendering"
__logger_logdir = os.path.expandvars("$HOME/.amira_blender_rendering")
__logger_filename = os.path.join(__logger_logdir, f"{__logger_name}.log")
__logger_loglevel = logging.INFO


def get_logger():
    """This function returns a logger instance."""

    # create directory of necessary
    if not os.path.exists(__logger_logdir):
        os.mkdir(__logger_logdir)

    # setup logger once. Note that basicConfig does nothing (as stated in the
    # documentation) if the root logger was already setup. So we can basically
    # re-call it here as often as we want.
    logging.basicConfig(level=__logger_loglevel,
            format="{} {} | {}, {}:{} | {}".format(
                "%(asctime)s",
                "%(levelname)s",
                "%(filename)s",
                "%(funcName)s",
                "%(lineno)d",
                "%(message)s",
            ),
            filename = __logger_filename)
    return logging.getLogger(__logger_name)


def set_level(logger, level="debug"):
    """Set the log level of a logger from a string.

    This is useful in combination with command line arguments."""

    if "debug" == level.lower():
        logger.setLevel(logging.DEBUG)
    elif "info" == level.lower():
        logger.setLevel(logging.INFO)
    elif "warning" == level.lower() or "warn" == level.lower():
        logger.setLevel(logging.WARNING)
    elif "error" == level.lower():
        logger.setLevel(logging.ERROR)
    elif "critical" == level.lower():
        logger.setLevel(logging.CRITICAL)
    elif "disable" == level.lower():
        logger.setLevel(logging.CRITICAL + 1)
    else:
        try:
            logger.setLevel(level)
        except ValueError:
            logger.warning('unsupported level "{}"'.format(level))



