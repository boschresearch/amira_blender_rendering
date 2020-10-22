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

"""
Script to be used to compute recitifed, i.e.. rectilinear, depth map starting from
pinhole depth map.

Depth values for perfect pinhole camera models are computed always with respect to the pinhole of the camera.
For this reason, points with equal depth always lay in a sphere around and centered at the pinhole.
Points on planes parallel to the image plane will have different depth values.

Conversely, in standard rasterization models, points on planes parallel to the image plane share the same depth.
This is becasue during standard rasterization, the view frustum (laying between the near and the far plane,
with the near plane being ~= camera image plane) is rectified into a parallelepiped volume.

Because of this discrepancy, depth values of pinhole camera models might need to be rectified in some applications.
"""

import sys
import os
import argparse


def _err_msg():
    return """Error: Could not import amira_blender_rendering.
Either install it as a package, or specify a valid path to its location with the --abr-path command line argument."""


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def import_abr(path=None):
    """(Try to) import amira_blender_rendering.

    This function tries to import amira_blender_rendering, either from python's
    installed packages (if path=None), or from a path (str). The reason this
    import happens this way is that the script this function belongs to is run
    from within blender, which might not have access to pip-installed packages.
    In this case, we need to specify an explicit path and add it to python's
    search path.

    Args:
        path (str): None, or path to amira_blender_rendering.
    """
    global abr, expandpath, BaseConfiguration, camera_utils

    if path is None:
        try:
            import amira_blender_rendering as abr
        except ImportError:
            print(_err_msg())
            sys.exit(1)
    else:
        abr_path = os.path.expanduser(os.path.expandvars(path))
        if not os.path.exists(abr_path):
            print(_err_msg())
            sys.exit(1)
        sys.path.append(abr_path)
        try:
            import amira_blender_rendering as abr
        except ImportError:
            print(_err_msg())
            sys.exit(1)

    # import additional parts
    from amira_blender_rendering.utils.io import expandpath
    from amira_blender_rendering.scenes.baseconfiguration import BaseConfiguration
    import amira_blender_rendering.utils.camera as camera_utils


def get_cmd_argparser():
    parser = argparse.ArgumentParser(description='Compute rectified depth map of a given dataset')

    parser.add_argument('path', help='Path to dataset directory to convert')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite depth files')

    parser.add_argument('-abr', '--abr-path', dest='abr_path',
                        default='~/amira_blender_rendering/src',
                        help='Path where amira_blender_rendering (abr) can be found')

    parser.add_argument('-c', '--config', help='Path to config file')
    
    return parser


def main():

    parser = get_cmd_argparser()
    args = parser.parse_known_args(args=get_argv())[0]

    import_abr(args.abr_path)

    if not os.path.exists(args.path) and not os.path.isdir(args.path):
        raise RuntimeError(f'Path "{args.path}" does not exists or is not a directory')

    dirpath_depth = os.path.join(args.path, 'Images', 'depth')
    dirpath_depth_rect = dirpath_depth
    if not args.overwrite:
        dirpath_depth_rect = os.path.join(args.path, 'Images', 'depth_rectilinear')
        if not os.path.exists(dirpath_depth_rect):
            os.mkdir(dirpath_depth_rect)

    # get and parse config
    config = BaseConfiguration()
    config_filepath = os.path.join(expandpath(args.path), 'Dataset.cfg')
    if args.config is not None:
        config_filepath = expandpath(args.config)
        if not os.path.exists(config_filepath):
            raise RuntimeError(f'File {config_filepath} does not exists')
    config.parse_file(config_filepath)

    # get specific configs
    res_x = config.camera_info.width
    res_y = config.camera_info.height
    sensor_width = config.camera_info.sensor_width
    f_in_mm = config.camera_info.focal_length

    # loop over files
    for fname in os.listdir(dirpath_depth):
        fpath = os.path.join(dirpath_depth, fname)
        outfpath = os.path.join(dirpath_depth_rect, fname)
        camera_utils.project_pinhole_depth_to_rectilinear(fpath, outfpath, res_x, res_y, sensor_width, f_in_mm)


if __name__ == '__main__':
    main()
