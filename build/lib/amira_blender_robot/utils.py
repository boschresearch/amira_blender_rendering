import os
# import errno
import logging
import os.path as osp

logger_name = "amira_blender_robot"


def get_logger(stream=True):
    logger = logging.getLogger(logger_name)
    if stream:
        stream_log(logger)
    return logger


def stream_log(logger):
    """Attaches a verbose stream handler"""

    for k in logger.handlers:
        if isinstance(k, logging.StreamHandler):
            return

    handler = logging.StreamHandler()

    message_format = logging.Formatter("{} {} | {} {} line {} | {}".format(
        "%(asctime)s",
        "%(levelname)s",  # PID?
        "%(filename)s",
        "%(funcName)s",
        "%(lineno)d",
        "%(message)s",
    ))
    handler.setFormatter(message_format)

    logger.addHandler(handler)
    logger.info("created verbose stream logger")


def set_level(logger, level="debug"):

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


# def check_input_file_exists(input_file, parent=""):
#     """Check input file, can be full path or file inside parent directory
#     :param input_file: .dae file
#     :param parent: optional parent folder
#     :return: full path to input file
#     """
#     # TODO: check file type by suffix
#     if osp.isfile(input_file):
#         return input_file
#     else:
#         full = osp.join(parent, input_file)
#         if osp.isfile(full):
#             return full
#         else:
#             explanation = "{} neither {}".format(input_file, full)
#             raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), explanation)


def get_my_dir(my_path):
    fullpath = osp.abspath(osp.realpath(my_path))
    if osp.isfile(fullpath):
        return osp.split(fullpath)[0]
    return fullpath


def try_func(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except Exception as err:
        logger = get_logger()
        logger.warning(print(err))


@try_func
def try_makedirs(fullpath):
    os.makedirs(fullpath)
