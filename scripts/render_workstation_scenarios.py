#!/usr/bin/env python

"""This script can be used to generate the workstation scenario datasets.

The script must be run in blender, for instance from the command line using:

    $ blender -b -P scripts/render_workstation_scenarios.py -- other-params

Example:

    $ blender -b -P scripts/render_workstation_scenarios.py -- --arb-path ~/amira/amira_blender_rendering --aps-path ~/amira/amira_perception

"""

# TODO
# At the moment, this is mostly a copy-paste of render_dataset_RenderedObjects,
# but adapted to the Workstation Scenarios and in particular the blender file,
# which contains multiple scenarios at once.  This should be unified at some
# point, if possible.

import bpy
import sys
import os
import argparse
import numpy as np
import random
from math import log, ceil


# TODO: a duplicate of this function lives in amira_blender_rendering.utils.
#       Because this might get loaded after first use of expanduser, we keep
#       this here, too.
def expandpath(path): # {{{
    return os.path.expandvars(os.path.expanduser(path))
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


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def get_cmd_argparser():
    parser = argparse.ArgumentParser(
        description='Render dataset in blender', prog="blender -b -P " + __file__,
        add_help=False)
    parser.add_argument('--config', default='config/render_toolcap.cfg', help='Path to configuration file')
    parser.add_argument('--aps-path', default='~/dev/vision/amira_perception',
                        help='Path where AMIRA Perception Subsystem (aps) can be found')
    parser.add_argument('--abr-path', default='~/dev/vision/amira_blender_rendering/src',
                        help='Path where amira_blender_rendering (abr) can be found')
    parser.add_argument('--only-viewsphere', action='store_true', help='Generate only Viewsphere dataset')
    parser.add_argument('--print-config', action="store_true", help='Print configuration and exit')
    parser.add_argument('-h', '--help', action='store_true', help='Print this help message and exit')

    return parser


# TODO
# maybe allow registration of configurations similar to the process in APS
def get_basic_config():
    "Setup script specific configuration"

    # basic config parameters
    config = abr.datastructures.Configuration()

    # general dataset configuration
    config.add_param('dataset.image_count', 0, 'Number of images to generate')
    config.add_param('dataset.output_path', '', 'Path to storage directory')

    # camera configuration
    config.add_param('camera_info.name', 'none', 'Name for camera')
    config.add_param('camera_info.width', 640, 'Rendered image resolution (pixel) along x (width)')
    config.add_param('camera_info.height', 480, 'Rendered image resolution (pixel) along y (height)')

    # render and scenario configuration
    config.add_param('render_setup.backend', 'blender-cycles', 'Render backend. Blender only one supported')
    config.add_param('render_setup.target_objects', '', '(List of) target objects in the scene', special='maybe_list')
    config.add_param('render_setup.blend_file', '~/gfx/modeling/workstation_scenarios.blend', 'Path to .blend file with modeled scene')

    # currently, the scenarios are simply enumerated from 0 - 5 (have a look at
    # the .blend file)
    config.add_param('render_setup.scenario', 0, 'Scene type to be rendered')
    config.add_param('render_setup.cameras', 'lcr', 'String containing which of the cameras to render (l = left, c = center, r = right)')

    return config


def main():
    # parse command arguments
    cmd_parser = get_cmd_argparser()
    cmd_args = cmd_parser.parse_args(args=get_argv())  # need to parse to get aps and abr

    # TODO: fix hard paths, and read configuration from file
    import_abr(expandpath('~/amira/amira_blender_rendering/src'))
    config = get_basic_config()

    # combine parsers and parse
    parser = argparse.ArgumentParser(
        prog="blender -b -P " + __file__,
        parents=[cmd_parser] + config.get_argparsers(),
        add_help=False)
    args = parser.parse_args(args=get_argv())

    # check if there's a config file
    if ('config' in args) and (args.config is None):
        print("Please specify a configuration file with the '--config' argument.")
        parser.print_help()
        sys.exit()

    # check if the configuration file exists
    configfile = expandpath(args.config)
    if not os.path.exists(configfile):
        raise RuntimeError(f"Configuration file '{configfile}' does not exist")



if __name__ == "__main__":
    main()
