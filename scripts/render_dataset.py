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


def expandpath(path): # {{{
    """Expand all variables and users in a path"""
    return os.path.expandvars(os.path.expanduser(path))
    # }}}


def import_abr(path=None): # {{{
    """Import amira_blender_rendering."""
    if path is not None:
        sys.path.append(expandpath(path))

    global abr, WorkstationScenarios, WorkstationScenariosConfiguration
    import amira_blender_rendering as abr
    import amira_blender_rendering.dataset
    import amira_blender_rendering.utils.blender as blender_utils
    import amira_blender_rendering.scenes
    from amira_blender_rendering.scenes.workstationscenarios import WorkstationScenarios, WorkstationScenariosConfiguration
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
            default='config/workstation_scenario01.cfg',
            help='Path to configuration file')

    parser.add_argument(
            '--abr-path',
            default='~/amira/amira_blender_rendering/src',
            help='Path where amira_blender_rendering (abr) can be found')

    parser.add_argument(
            'scenario',
            help='Scenario to generate dataset for')

    parser.add_argument(
            '--viewsphere',
            action='store_true',
            help='Generate Viewsphere instead of RenderedObjects dataset')

    parser.add_argument(
            '--list-scenes',
            action='store_true',
            help='Print list of scenes and exit')

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


def get_scene_types():
    from amira_blender_rendering.scenes.workstationscenarios import WorkstationScenarios, WorkstationScenariosConfiguration

    # each scenario consists of a name, and a tuple containing the scenario as
    # well as its configuration
    return {'WorkstationScenarios': [WorkstationScenarios, WorkstationScenariosConfiguration]}

def get_scene_type(type_str: str):
    """Get the (literal) type of a scene given a string.

    Essentially, this is what literal_cast does in C++, but for user-defined
    types.

    Args:
        type_str(str): type-string of a scene without module-prefix

    Returns:
        type corresponding to type_str
    """
    # specify mapping from str -> type to get the scene
    # TODO: this might be too simple at the moment, because some scenes might
    #       require more arguments. But we could think about passing along a
    #       Configuration object, similar to whats happening in aps
    scene_types = {
        'SimpleToolCap': abr.scenes.SimpleToolCap,
        'SimpleLetterB': abr.scenes.SimpleLetterB,
        'PandaTable': abr.scenes.PandaTable,
        'ClutteredPandaTable': abr.scenes.ClutteredPandaTable,
        'MultiObjectsClutteredPandaTable': abr.scenes.MultiObjectsClutteredPandaTable
    }
    if type_str not in scene_types:
        known_types = str([k for k in scene_types.keys()])[1:-1]
        raise Exception(f"Scene type {type_str} unknown. Known types: {known_types}. Note: types are case sensitive.")
    return scene_types[type_str]


def main():
    # parse command arguments
    cmd_parser = get_cmd_argparser()
    cmd_args = cmd_parser.parse_args(args=get_argv())  # need to parse to get aps and abr

    # TODO: this can be removed as soon as we have an installable abr
    # check if user specified abr_path
    if cmd_args.abr_path is None:
        print("Please specify the path under which the amira_blender_rendering python package (abr) can be found.")
        print("Note that abr should be found below the repository's src/ directory")
        sys.exit(1)

    abr_path = expandpath(cmd_args.abr_path)
    if not os.path.exists(abr_path):
        print("Please specify a valid path under which the amira_blender_rendering python package (abr) can be found.")
        print("Note that abr should be found below the repository's src/ directory")
        sys.exit(1)

    if cmd_args.list_scenes:
        scenarios = get_scenario_dict()

    scenario = cmd_args.scenario

    import_abr(expandpath(cmd_args.abr_path))
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
