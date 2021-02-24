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

"""Utility functions for IO and os.path operations"""

import bpy
import os
import os.path as osp
import shutil
from amira_blender_rendering.utils.logging import get_logger


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


def get_my_dir(my_path):
    fullpath = osp.abspath(osp.realpath(my_path))
    if osp.isfile(fullpath):
        return osp.split(fullpath)[0]
    return fullpath


def __try_func(func, *args, **kwargs):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as err:
            logger = get_logger()
            logger.warning(str(err))

    return wrapper


@__try_func
def try_makedirs(path):
    """Try to make a directory"""
    os.makedirs(path)


@__try_func
def try_rmtree(path):
    """Try to remove a file tree"""
    shutil.rmtree(path)


@__try_func
def try_move(src, dst):
    """Try to move a path from src to dst"""
    shutil.move(src, dst)


def write_numpy_image_buffer(buf, filepath_out):
    """Write numpy array `buf` of size WxH to a grayscale PNG image with 16bit
    color depth at location `filepath_out`.

    Args:
        buf (np.ndarray): WxH numpy array (i.e. single channel)
        filepath_out (str): Path to target file
    """

    # get width and height from the numpy array
    width, height = buf.shape

    # We need a temporary image buffer in blender to save the image to file.
    # Remove this temporary file first, if it already exists, then attempt
    # to create it
    buf_name = 'temporary_output_buffer.png'
    if buf_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[buf_name])
    bpy.data.images.new(buf_name, width=width, height=height, alpha=False, float_buffer=False)

    # store current color mode and depth
    prev_color_mode  = bpy.context.scene.render.image_settings.color_mode
    prev_color_depth = bpy.context.scene.render.image_settings.color_depth
    try:
        # temporarily toggle the render output image format, as we'll use save_render below for writing the PNG
        bpy.context.scene.render.image_settings.color_mode = 'BW'
        bpy.context.scene.render.image_settings.color_depth = '16'

        output = bpy.data.images[buf_name]
        output.file_format = 'PNG'

        # convert ('blow-up') back to RGBA pixels, required for blender's Image struct, and set Alpha to 1.0
        buf_rgba = np.repeat(buf[:, :, np.newaxis], 4, axis=2)
        buf_rgba[:, :, 3] = 1.0
        output.pixels = buf_rgba.ravel()
        # use save_render, because this way we get the image_settings applied to the PNG file. Unfortunately, there
        # doesn't seem to be another way to set the color mode and depth for a PNG that gets written to
        # a file.
        output.save_render(filepath=filepath_out)

    finally:
        # reset color mode and depth, remove buffer image
        bpy.context.scene.render.image_settings.color_mode = prev_color_mode
        bpy.context.scene.render.image_settings.color_depth = prev_color_depth
        if buf_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[buf_name])


def read_numpy_image_buffer(filepath_in, check_exr_format = False):
    """Read an image into a numpy buffer.

    Note that this method will only return the first channel of the input image,
    as it is currently used to load grayscale PNG images or range values from
    OpenEXR files. If there are additional channels required, this function must
    be extended / change accordingly.

    Args:
        filepath_in (str): path to the file
        check_exr_format (bool): Check if the file format really was OpenEXR

    Returns:
        np.ndarray of size WxH
    """

    # sanity check
    if not os.path.exists(filepath_in):
        raise ValueError(f"File {filepath_in} does not exist. Please check path")

    # load/reload image data if the filename is already available within blender
    filename_in = os.path.basename(filepath_in)
    image_added = False
    if filename_in in bpy.data.images:
        bpy.data.images[filename_in].reload()
    else:
        bpy.ops.image.open(filepath=filepath_in)
        image_added = True

    # check file format if requested
    if check_exr_format:
        img_data = bpy.data.images[filename_in]
        fformat = img_data.file_format
        if not fformat == 'OPEN_EXR':
            raise ValueError(f"Invalid image format. Expected OPEN_EXR, got 'f{format}'.")

    # get access to blender's Image struct. This will be an RGBA image
    img_data = bpy.data.images[filename_in]
    # extract the first channel of the PNG image
    width = img_data.size[0]
    height = img_data.size[1]
    buf = np.array(img_data.pixels[:], dtype=np.float32)
    buf = buf.reshape(width, height, img_data.channels)
    buf = buf[:,:,0]

    # remove the image if it was created
    if image_added:
        bpy.data.images.remove(bpy.data.images[filename_in])

    return buf

