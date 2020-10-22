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


import os
import pkgutil
import importlib


# generic auto import method
def _auto_import(pkgname: str, dirname: str, subdirs: list, ):
    """
    Implement module autoimports to specified directories and subdirectories
    NOTE: import and call from the pkg __init__.py

    Args:
        pkgname(str): name of caller pkg.
        dirname(str): top most directory of pkg to import.
        subdirs(list(str)): list of subdirectories to import.

    Example usage:
        Assume you have a pkg with the following filsystem struct
        + package:
        |__ __init__.py
        |__ subdir1
        |__ subdir2
        |__ subdir3
        
        and you want to import subdir1 and subdir2. Then, within package/__init__.py:

        from aps import _auto_import
        _auto_import(pkgname=__name__, dirname=os.path.dirname(__file__), subdirs=['subdir1', 'subdir2'])
    """
    for subdir in subdirs:
        dir = os.path.realpath(os.path.join(dirname, subdir))
        for importer, module_name, ispkg in pkgutil.iter_modules([dir]):
            if not ispkg:
                # the if condition is to make sure the import works also withing a pkg where
                # subdir == ''
                if subdir:
                    importlib.import_module(f".{subdir}.{module_name}", pkgname)
                else:
                    importlib.import_module(f".{module_name}", pkgname)
