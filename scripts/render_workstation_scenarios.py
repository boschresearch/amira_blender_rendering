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

    global abr, WorkstationScenarios, WorkstationScenariosConfiguration
    import amira_blender_rendering as abr
    import amira_blender_rendering.dataset
    import amira_blender_rendering.blender_utils
    import amira_blender_rendering.scenes
    from amira_blender_rendering.scenes.workstationscenarios import WorkstationScenarios, WorkstationScenariosConfiguration
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

    parser.add_argument(
            '--config',
            default='config/workstation_scenarios.cfg',
            help='Path to configuration file')

    parser.add_argument(
            '--aps-path',
            default='~/amira/amira_perception',
            help='Path where AMIRA Perception Subsystem (aps) can be found')

    parser.add_argument(
            '--abr-path',
            default='~/amira/amira_blender_rendering/src',
            help='Path where amira_blender_rendering (abr) can be found')

    parser.add_argument(
            '--only-viewsphere',
            action='store_true',
            help='Generate only Viewsphere dataset')

    parser.add_argument(
            '--print-config',
            action="store_true",
            help='Print configuration and exit')

    parser.add_argument(
            '-h',
            '--help',
            action='store_true',
            help='Print this help message and exit')

    return parser

def main():
    # parse command arguments
    cmd_parser = get_cmd_argparser()
    cmd_args = cmd_parser.parse_args(args=get_argv())  # need to parse to get aps and abr

    # TODO: fix hard paths, and read configuration from file
    import_abr(expandpath('~/amira/amira_blender_rendering/src'))
    config = WorkstationScenariosConfiguration()

    # combine parsers and parse command line arguments
    parser = argparse.ArgumentParser(
        prog="blender -b -P " + __file__,
        parents=[cmd_parser] + config.get_argparsers(),
        add_help=False)
    args = parser.parse_args(args=get_argv())

    # check if the configuration file exists
    configfile = expandpath(args.config)
    if not os.path.exists(configfile):
        raise RuntimeError(f"Configuration file '{configfile}' does not exist")

    # parse configuration from file, and then update with arguments
    config.parse_file(configfile)
    config.parse_args()

    # build split configuration
    splitting_configs = abr.dataset.build_splitting_configs(config)

    # start generating datasets
    for cfg in splitting_configs:
        scene = WorkstationScenarios(config=config)
        if scene.generate_dataset():
            # save configuration alongside the dataset
            # abr.dataset.dump_config(cfg, expandpath(cfg.dataset.base_path))
            print(f"II: Success")
        else:
            print(f"EE: Error while generating dataset")


if __name__ == "__main__":
    main()
