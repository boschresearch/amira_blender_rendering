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
from functools import partial


# generic auto import method
def _auto_import(pkgname: str, dirname: str, subdirs: list, ):
    """
    Implement module similar to src.amira_blender_rendering.cli
    """
    # if subdirectory list is empty list all avalilable
    if not subdirs:
        subdirs = [d for d in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, d)) and not d.startswith('__')]
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


# init dictionary of available tests
_available_tests = {}


def register(name: str):
    """Register a class/function to the specified test group name

    NOTE: it is good practice to register all tests belonging to the same subfolder
    under the same name. Such name usually coincides with the subfolder name.
    As an example, see tests files/classes in tests/math subfolder.
    This is not mandatory but it helps keeping multiple test classes under the group
    they ideally should belong to.

    This function should be used as a class decorator:

    ..code::
        @register_test(name='awesome_sauce')
        class AnotherClass(MyClass):
            def __init__(self, ...)
            ...

    Args:
        name(str): Name for the test group the test is added to

    Returns:
        The class that was passed as argument.

    Raises:
        ValueError: if invalid(none) name given.
    """
    def _register(obj, name):
        if name is None:
            raise ValueError(f'Provide an appropriate name for the current scene of type {obj.__name__.lower()}')
        if name not in _available_tests:
            _available_tests[name] = []
        # append tests with the same name (e.g. contained in the same test module)
        _available_tests[name].append(obj)
        return obj
    return partial(_register, name=name)


def get_registered(name: str = None):
    """
    Return all or a subset of registered tests (using register_test method)

    Args:
        name(str): name of registered group of tests to query

    Returns:
        if None given as input: a dictionary with all tests groups
        if a correct name for a test group given as input: a list with registered tests contained in the group
    """
    if name is None:
        return _available_tests
    if name not in _available_tests:
        raise ValueError(f'Queried type "{name}" not among availables: {list(_available_tests.keys())}')
    return _available_tests[name]


_auto_import(pkgname=__name__, dirname=os.path.dirname(__file__), subdirs=[])
