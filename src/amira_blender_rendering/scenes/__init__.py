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

"""The scenes module contains scene managers for various setups."""

# base classes
from .basescenemanager import BaseSceneManager  # noqa
from .baseconfiguration import BaseConfiguration  # noqa
from .threepointlighting import ThreePointLighting  # noqa
from .basescene import BaseABRScene  # noqa

# composition classes, if inheritance should or cannot be used
from .rendermanager import RenderManager  # noqa

# concrete scenes are autoimported later at the end of the file
import os
from functools import partial
from amira_blender_rendering.cli import _auto_import

_available_scenes = {}


def register(name: str, type: str = None):
    """Register a class/function to the specified available type.

    This function should be used as a class decorator:

    The name should be unique for the scene type that is being registered.

    ..code::
        @register(name='awesome_sauce', type)
        class AnotherClass(MyClass):
            def __init__(self, ...)
            ...

    Args:
        name(str): Name for the scene to register
        type(str): Either 'scene' or 'config' depending wheter the actual scene class
            or the corresponding configuration class is registered

    Returns:
        The class that was passed as argument.

    Raises:
        ValueError: if invalid name/type given.
    """
    def _register(obj, name, obj_type):
        if obj_type not in ['scene', 'config']:
            raise ValueError(f'Requested type {obj_type} is not available')
        if name is None:
            raise ValueError(f'Provide an appropriate name for the current scene of type {obj.__name__.lower()}')
        if name not in _available_scenes:
            _available_scenes[name] = dict()
        _available_scenes[name][obj_type] = obj
        return obj
    return partial(_register, name=name, obj_type=type)


def get_registered(name: str = None):
    """
    Return dictionary of available classes/function type registered via register(name, type)
    
    Args:
        name(str): name of registered object to query
    """
    if name is None:
        return _available_scenes
    if name not in _available_scenes:
        raise ValueError(f'Queried type "{name}" not among availables: {list(_available_scenes.keys())}')
    return _available_scenes[name]


_auto_import(pkgname=__name__, dirname=os.path.dirname(__file__), subdirs=[''])
