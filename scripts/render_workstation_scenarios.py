#!/usr/bin/env python

"""This script can be used to generate the workstation scenario datasets.

The script must be run in blender, for instance from the command line using:

    $ blender -b -P scripts/render_workstation_scenarios.py -- other-params

Example:

    $ blender -b -P scripts/render_workstation_scenarios.py -- --arb-path ~/amira/amira_blender_rendering --aps-path ~/amira/amira_perception

"""

# TODO: at the moment, this is mostly a copy-paste of
# render_dataset_RenderedObjects. This needs to be unified at some point, but
# the workstation dataset is probably significantly different from the other
# dataset such that a separate strain of development is easier in the beginning.

import bpy
import sys
import os
import argparse
import numpy as np
import random
from math import log, ceil


def expandpath(path): # {{{
    return os.path.expandvars(os.path.expanduser(path))
    # }}}

def import_aps(path=None): # {{{
    """Import the AMIRA Perception Subsystem."""
    if path is not None:
        sys.path.append(expandpath(path))

    global aps
    global foundry
    global RenderedObjects

    import aps
    import aps.core
    from aps.data.datasets.renderedobjects import RenderedObjects

    import foundry
    import foundry.utils

    # additional
    # global ViewSampler
    # from aps.data.utils.viewspheresampler import ViewSampler
    # }}}

def import_abr(path=None): # {{{
    """Import amira_blender_rendering."""
    if path is not None:
        sys.path.append(expandpath(path))

    global abr
    import amira_blender_rendering as abr
    import amira_blender_rendering.blender_utils
    import amira_blender_rendering.scenes
    # }}}

def get_environment_textures(cfg): # {{{
    """Determine if the user wants to set specific environment texture, or
    randomly select from a directory

    Args:
        cfg(Configuration): config with render setup
    """
    # this rise a KeyError if 'environment_texture' not in cfg
    environment_textures = expandpath(cfg.environment_texture)
    if os.path.isdir(environment_textures):
        files = os.listdir(environment_textures)
        environment_textures = [os.path.join(environment_textures, f) for f in files]
    else:
        environment_textures = [environment_textures]

    return environment_textures
    # }}}



def get_basic_config():
    "Setup script specific configuration"

    # basic config parameters
    config = aps.core.utils.datastructures.Configuration()


def main():
    # TODO: fix hard paths
    import_aps(expandpath('~/amira/amira_perception'))
    import_abr(expandpath('~/amira/amira_blender/rendering'))

    # TODO: read config from file



if __name__ == "__main__":
    main()
