#!/usr/bin/env python

"""Utility functions for IO and os.path operations"""

import os
import shutil
from amira_blender_rendering.utils.logging import get_logger

def expandpath(path, check_file=False):
    """Expand global variables and users given a path or a list of paths.

    Args:
        path (str or list): path to expand

    Returns:
        Expanded path
    """
    if isinstance(path, str):
        path = os.path.expanduser(os.path.expandvars(path))
        if not check_file or os.path.exists(path):
            return path
        else:
            raise FileNotFoundError(f'Path {path} does not exist - are all environment variables set?')
    elif isinstance(path, list):
        return [expandpath(p) for p in path]



def get_my_dir(my_path):
    fullpath = osp.abspath(osp.realpath(my_path))
    if osp.isfile(fullpath):
        return osp.split(fullpath)[0]
    return fullpath


def __try_func(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as err:
            logger = get_logger()
            logger.warning(str(err))

    return wrapper


@__try_func
def try_makedirs(path):
    """Try to make a directory"""
    os.makedirs(path)


@__try_func
def try_rmtree(path):
    """Try to remove a file tree"""
    shutil.rmtree(path)


@__try_func
def try_move(src, dst):
    """Try to move a path from src to dst"""
    shutil.move(src, dst)


