#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import logging


# Logging configs
__logger_name = "abr_dataset_tools"
__logger_loglevel = logging.INFO

__basic_format = "{} {} | {}, {}:{} | {}".format(
    "%(asctime)s",
    "%(levelname)s",
    "%(filename)s",
    "%(funcName)s",
    "%(lineno)d",
    "%(message)s",
)


def get_logger(level=__logger_loglevel, fmt=None):
    """This function returns a logger instance.

    If coloredlogs is installed the messages in terminal will have different colors acording to logging level.
    If verboselogs is installed ist supports additional logging levels and color variations.

    Args:
        level (str, optional): logging level. Defaults to "INFO".
        fmt (str, optional): message format template: fields, order, etc. Defaults to None, which uses a "basic_format".

    Returns:
        logging.Logger: a logger instance.
    """
    # we log directly to sys.stdout

    # setup logger once. Note that basicConfig does nothing (as stated in the
    # documentation) if the root logger was already setup. So we can basically
    # re-call it here as often as we want.
    if fmt is None:
        fmt = __basic_format

    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format=fmt
    )

    logger = logging.getLogger(__logger_name)

    return logger
