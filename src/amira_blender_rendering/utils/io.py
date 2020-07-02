#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
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


