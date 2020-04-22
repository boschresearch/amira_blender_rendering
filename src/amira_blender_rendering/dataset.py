#!/usr/bin/env python

"""
This file contains functions that are required to generate a dataset, or to add
things to certain scenarios which has an impact on the generated dataset.
"""

import os
from math import ceil
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.datastructures import DynamicStruct


def get_environment_textures(base_path):
    """Determine if the user wants to set specific environment texture, or
    randomly select from a directory

    Args:
        cfg(Configuration): config with render setup
    """
    # this rise a KeyError if 'environment_texture' not in cfg
    environment_textures = expandpath(base_path)
    if os.path.isdir(environment_textures):
        files = os.listdir(environment_textures)
        environment_textures = [os.path.join(environment_textures, f) for f in files]
    else:
        environment_textures = [environment_textures]

    return environment_textures


#
#
# NOTE: the functions and classes below were partially taken from amira_perception. Make
#       sure to keep in sync as long as we don't have a core library that is
#       restricted to such functionality
#
#

def build_directory_info(base_path: str, **kwargs):
    """Build a dynamic struct with the directory configuration of a RenderedObject dataset.

    The base_path should be expanded and not contain global variables or
    other system dependent abbreviations.

    Args:
        base_path (str): path to the root directory of the dataset
        **dense_features(bool): true if database contains a dense feature representation of the object
    """

    # initialize
    dir_info = DynamicStruct()
    dir_info.images = DynamicStruct()
    dir_info.annotations = DynamicStruct()

    # setup all path related information
    dir_info.base_path             = expandpath(base_path)
    dir_info.annotations.base_path = os.path.join(dir_info.base_path             , 'Annotations')
    dir_info.annotations.opengl    = os.path.join(dir_info.annotations.base_path , 'OpenGL')
    dir_info.annotations.opencv    = os.path.join(dir_info.annotations.base_path , 'OpenCV')
    dir_info.images.base_path      = os.path.join(dir_info.base_path             , 'Images')
    dir_info.images.const          = os.path.join(dir_info.images.base_path      , 'rgb')
    dir_info.images.random         = os.path.join(dir_info.images.base_path      , 'random_light')
    dir_info.images.depth          = os.path.join(dir_info.images.base_path      , 'depth')
    dir_info.images.mask           = os.path.join(dir_info.images.base_path      , 'mask')

    dense_features = kwargs.get('dense_features', False)
    if dense_features:
        dir_info.images.dense_features = os.path.join(dir_info.images.base_path, 'dense_features')

    return dir_info


def dump_config(cfg, output_path):
    """Dumps the configuration to the output directory"""

    # TODO: store everything we know about the camera setup
    filepath = os.path.join(output_path, "Dataset.cfg")
    with open(filepath, 'w') as cfg_file:
        cfg_file.write(cfg.to_cfg())


def check_paths(cfg):
    """expand variables and check if files exist"""

    if 'model' in cfg['dataset']:
        cfg['dataset']['model'] = expandpath(cfg['dataset']['model'])
        if not os.path.isfile(cfg['dataset']['model']):
            raise Exception("Model file '{}' does not exist".format(cfg['dataset']['model']))

    if 'output_path' in cfg['dataset']:
        cfg['dataset']['output_path'] = expandpath(cfg['dataset']['output_path'])

    if 'camera_calibration' in cfg['camera_info']:
        cfg['camera_info']['camera_calibration'] = expandpath(cfg['camera_info']['camera_calibration'])
        if not os.path.isfile(cfg['camera_info']['camera_calibration']):
            raise Exception(
                "Camera calibration file '{}' does not exist".format(cfg['camera_info']['camera_calibration']))

    return cfg

