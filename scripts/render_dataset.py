#!/usr/bin/env python

"""This script can be used to generate the workstation scenario datasets.

The script must be run in blender, for instance from the command line using:

    $ blender -b -P scripts/render_dataset.py -- other-params

Example:

    $ blender -b -P scripts/render_dataset.py -- --abr-path ~/amira/amira_blender_rendering

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
import logging
from math import log, ceil


# NOTE: this is a copy of src/amira_blender_rendering/utils/io.py#expandpath.
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


def import_abr(path=None): # {{{
    """(Try to) import amira_blender_rendering."""

    global abr, WorkstationScenarios, WorkstationScenariosConfiguration

    if path is None:
        try:
            import amira_blender_rendering as abr
        except:
            print("Error: Could not import amira_blender_rendering. Either install it as a")
            print("       package, or specify the path to its location with the --abr-path")
            print("       command line argument. Example:")
            print("          $ blender -b -P scripts/render_dataset.py -- --abr-path ./src")
            print("       For more help, see documentation, or invoke with --help")
            sys.exit(1)
    else:
        abr_path = expandpath(path, check_file=True)
        sys.path.append(expandpath(abr_path))
        try:
            import amira_blender_rendering as abr
        except:
            print("Error: amira_blender_rendering not found during import. Did you pass")
            print("       the wrong path?")
            sys.exit(1)

    import amira_blender_rendering.dataset
    import amira_blender_rendering.utils.blender as blender_utils
    import amira_blender_rendering.scenes
    from amira_blender_rendering.scenes.workstationscenarios import WorkstationScenarios, WorkstationScenariosConfiguration
    from amira_blender_rendering.utils.logging import get_logger
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
    # TODO: this could/should be handled with some internal registration
    #       mechanism that 'knows' all scenarios
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
    cmd_args = cmd_parser.parse_known_args(args=get_argv())[0]  # need to parse to get aps and abr
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
    argv = get_argv()
    args = parser.parse_args(args=argv)
    # show help only here, because this will include the help for the dataset
    # configuration
    if args.help:
        parser.print_help()
        sys.exit(0)

    # check if the configuration file exists
    configfile = expandpath(args.config, check_file=True)

    # parse configuration from file, and then update with arguments
    config.parse_file(configfile)
    config.parse_args(argv=argv)

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
        get_logger().error("Error while generating dataset")

    # tear down scene. should be handled by blender, but a scene might have
    # other things opened that it should close gracefully
    scene.teardown()

if __name__ == "__main__":
    main()
