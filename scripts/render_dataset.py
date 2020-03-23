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
import re
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
            default='config/workstation_scenario01_train.cfg',
            help='Path to configuration file')

    parser.add_argument(
            '--abr-path',
            default='~/amira/amira_blender_rendering/src',
            help='Path where amira_blender_rendering (abr) can be found')

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
    from amira_blender_rendering.scenes.simpletoolcap import SimpleToolCap, SimpleToolCapConfiguration

    # each scenario consists of a name, and a tuple containing the scenario as
    # well as its configuration
    return {
        'SimpleToolCap':
            [SimpleToolCap, SimpleToolCapConfiguration],
        'WorkstationScenarios':
            [WorkstationScenarios, WorkstationScenariosConfiguration]
        }


def determine_scene_type(config_file):
    """Determine the scene type given a configuration file."""
    # don't parse the entire ini file, only look for scene_type
    scene_type = None
    pattern = re.compile('^\s*scene_type\s*=\s*(.*)\s*$', re.IGNORECASE)
    with open(config_file) as f:
        for line in f:
            match = pattern.match(line)
            if match is not None:
                scene_type = match.group(1)
    if scene_type is None:
        raise RuntimeError("scene_type missing from configuration file. Is your config valid?")
    return scene_type


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
    import_abr(cmd_args.abr_path)

    # pretty print available scenarios?
    scene_types = get_scene_types()
    if cmd_args.list_scenes:
        print("List of possible scenes:")
        for k, _ in scene_types.items():
            print(f"   {k}")
        sys.exit(0)

    # change all keys to lower-case
    scene_types = dict((k.lower(), v) for k, v in scene_types.items())

    # check scene_type in config
    scene_type_str = determine_scene_type(cmd_args.config)
    if scene_type_str.lower() not in scene_types:
        raise RuntimeError(f"Invalid configuration: Unknown scene_type {scene_type_str}")

    # instantiate configuration
    config = scene_types[scene_type_str.lower()][1]()

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

    # instantiate the scene.
    # NOTE: we do not automatically create splitting configs anymore. You need
    #       to run the script twice, with two different configurations, to
    #       generate the split. This is significantly easier than internally
    #       maintaining split configurations.
    scene = scene_types[scene_type_str.lower()][0](config=config)

    # generate the dataset
    success = False
    if cmd_args.viewsphere:
        success = scene.generate_viewsphere_dataset()
    else:
        success = scene.generate_dataset()

    # after finishing, dump the configuration(s) to the target locations (which
    # might depend on scene-internal state)
    if success:
        scene.dump_config()
    else:
        print(f"EE: Error while generating dataset")

    # tear down scene. should be handled by blender, but a scene might have
    # other things opened that it should close gracefully
    scene.teardown()

if __name__ == "__main__":
    main()
