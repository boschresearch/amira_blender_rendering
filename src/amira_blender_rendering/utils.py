import os
import shutil
import logging
import os.path as osp

logger_name = "amira_blender_rendering"


def expandpath(path):
    return os.path.expandvars(os.path.expanduser(path))

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


def get_my_dir(my_path):
    fullpath = osp.abspath(osp.realpath(my_path))
    if osp.isfile(fullpath):
        return osp.split(fullpath)[0]
    return fullpath


def try_func(func, *args, **kwargs):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as err:
            logger = get_logger()
            logger.warning(str(err))

    return wrapper


@try_func
def try_makedirs(fullpath):
    os.makedirs(fullpath)


@try_func
def try_rmtree(fullpath):
    shutil.rmtree(fullpath)


@try_func
def try_move(src, dst):
    shutil.move(src, dst)
