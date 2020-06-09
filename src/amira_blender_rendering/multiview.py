
"""
export AMIRA_DATA_GFX='/home/pll1tv/PycharmProjects/amira_data_gfx'
(base) pll1tv@TV2ZOSD8:~/PycharmProjects/ActivePerception/create_synthetic_dataset$ blender -b -P blender_script.py
"""

import sys
import os
import bpy
import pathlib
from mathutils import Vector
import time
import random
from math import ceil, log
import re
import argparse
import logging
import numpy as np

sys.path.insert(1, '/home/pll1tv/PycharmProjects/amira_blender_rendering/src')

import amira_blender_rendering.interfaces as interfaces

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.datastructures import Configuration, flatten
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.interfaces as interfaces

#from amira_blender_rendering.scenes.workstationscenarios import WorkstationScenarios

from amira_blender_rendering.cli.render_dataset import get_cmd_argparser, get_scene_types, determine_scene_type, import_abr, get_argv

AMIRA_DATA_GFX = '/home/pll1tv/PycharmProjects/amira_data_gfx'

# parse command arguments
cmd_parser = get_cmd_argparser()
cmd_args = cmd_parser.parse_known_args(args=get_argv())[0]  # need to parse to get aps and abr
#import_abr(cmd_args.abr_path)
import_abr('~/PycharmProjects/amira_blender_rendering/src') #liadp
# pretty print available scenarios?
scene_types = get_scene_types()

# change all keys to lower-case
scene_types = dict((k.lower(), v) for k, v in scene_types.items())

# check scene_type in config
#scene_type_str = determine_scene_type(cmd_args.config)
scene_type_str = determine_scene_type('/home/pll1tv/PycharmProjects/amira_blender_rendering/config/workstation_scenario01_multiview_train.cfg') #liadp
if scene_type_str.lower() not in scene_types:
    raise RuntimeError(f"Invalid configuration: Unknown scene_type {scene_type_str}")

# instantiate configuration
config = scene_types[scene_type_str.lower()][1]()

# combine parsers and parse command line arguments
parser = argparse.ArgumentParser(
    prog="blender -b -P " + '~/PycharmProjects/amira_blender_rendering/src/amira_blender_rendering_cli/render_dataset.py',
    parents=[cmd_parser] + config.get_argparsers(),
    add_help=False)#liadp
argv = get_argv()
args = parser.parse_args(args=argv)
# show help only here, because this will include the help for the dataset
# configuration
if args.help:
    parser.print_help()
    sys.exit(0)

# check if the configuration file exists
configfile = expandpath('/home/pll1tv/PycharmProjects/amira_blender_rendering/config/workstation_scenario01_multiview_train.cfg', check_file=True)

# parse configuration from file, and then update with arguments
config.parse_file(configfile)
config.parse_args(argv=argv)

# instantiate the scene.
# NOTE: we do not automatically create splitting configs anymore. You need
#       to run the script twice, with two different configurations, to
#       generate the split. This is significantly easier than internally
#       maintaining split configurations.
scene = scene_types[scene_type_str.lower()][0](config=config)


scene.dump_config()

# generate the dataset
success = False
if cmd_args.viewsphere:
    success = scene.generate_viewsphere_dataset()
else:
    success = scene.generate_viewsphere_dataset()
    # success = scene.generate_dataset()
if not success:
    get_logger().error("Error while generating dataset")

# tear down scene. should be handled by blender, but a scene might have
# other things opened that it should close gracefully
scene.teardown()