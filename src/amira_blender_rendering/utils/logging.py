#!/usr/bin/env python

# logging setup

import logging

# local logger configuration
__logger_name = "amira_blender_rendering"
__logger_filename = "/tmp/amira_blender_rendering.log"
__logger_loglevel = logging.INFO


def get_logger():
    """This function returns a logger instance."""

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



