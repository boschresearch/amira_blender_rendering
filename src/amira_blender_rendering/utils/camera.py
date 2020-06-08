#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from mathutils import Vector, Matrix
import warnings
import numpy as np

def opencv_to_blender(K, cam, scale = 1.0):
    """Convert the intrinsic camera from OpenCV to blender's format

    Args:
        K (np.array): 3x3 intrinsic camera calibration matrix

    """

    warnings.warn('opencv_to_blender() is deprecated, use set_calibration_matrix() instead')

    if K is None:
        return cam

    sensor_width_mm  = K[1,1] * K[0,2] / (K[0,0] * K[1,2])
    sensor_height_mm = 1

    # assume principal point in center
    pixel_size_x = K[0,2] * 2
    pixel_size_y = K[1,2] * 2
    pixel_aspect = K[0,0] / K[1, 1]

    s_u = pixel_size_x / sensor_width_mm
    s_v = pixel_size_y / sensor_height_mm

    f_in_mm = K[0,0] / s_u

    scene = bpy.context.scene
    scene.render.resolution_x = pixel_size_x / scale
    scene.render.resolution_y = pixel_size_y / scale
    scene.render.resolution_percentage = scale * 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = pixel_aspect

    # set perspective camera
    cam.data.type = 'PERSP'
    cam.data.lens = f_in_mm
    cam.data.sensor_width = sensor_width_mm

    return cam


def opengl_to_opencv(v : Vector) -> Vector:
    """Turn a coordinate in OpenGL convention to OpenCV convention.

    OpenGL's (and blenders) coordinate system has x pointing right, y pointing
    up, z pointing backwards.

    OpenCV's coordinate system has x pointing right, y pointing down, z pointing
    forwards."""
    if len(v) != 3:
        raise Exception(f"Vector {p} needs to be 3 dimensional")

    return Vector((v[0], -v[1], -v[2]))


def get_sensor_fit(sensor_fit, size_x, size_y):
    # determine most likely sensor fit
    if sensor_fit == 'AUTO':
        return 'HORIZONTAL' if size_x >= size_y else 'VERTICAL'
    else:
        return sensor_fit


def get_calibration_matrix(scene, cam):
    """Compute the calibration matrix K for a given scene and camera.

    Args:
        scene (bpy.types.Scene): scene to operate on
        cam (bpy.types.Camera): camera to compute calibration matrix for
    """
    fx, fy, cx, cy = get_intrinsics(scene, cam)
    K = Matrix(((fx, 0, cx), (0, fy, cy), (0, 0, 1)))
    return K


def set_calibration_matrix(scene, cam, K):
    """Set the calibration matrix K of a camera cam in scene scene.

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        K (np.ndarray or mathutils.Matrix): 3x3 calibration matrix
    """
    if K is None:
        return cam
    if isinstance(K, np.ndarray):
        return _set_intrinsics(scene, cam, K[0, 0], K[1, 1], K[0, 2], K[1, 2])
    else:
        return _set_intrinsics(scene, cam, K[0][0], K[1][1], K[0][2], K[1][2])


def set_intrinsics(scene, cam, fx, fy, cx, cy):
    """Set the camera intrinsics of a camera.

    Note that the implementation is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://www.rojtberg.net/1601/from-blender-to-opencv-camera-and-back/ and
        3) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        fx (float): focal length in x direction
        fy (float): focal length in y direction
        cx (float): camera principal point coordinate X
        cy (float): camera principal point coordinate Y
    """
    render = scene.render

    # we assume a horizontal sensor with a default height of 1.0, so we only need to set one sensor size
    sensor_size_mm = fy * cx / (fx * cy)
    sensor_fit = 'HORIZONTAL'

    # we assume that the principal point is in the center of the camera
    resolution_x = cx * 2.0
    resolution_y = cy * 2.0
    pixel_aspect_ratio = fx / fy

    # compute focal lengths s_u, s_v
    s_u = resolution_x / sensor_size_mm
    s_v = resolution_y / 1.0

    # compute camera focal length in mm
    f_in_mm = fx / s_u

    # we assume that we render at 100% scale
    scale = 1.0

    # set render setup
    render.resolution_x = resolution_x / scale
    render.resolution_y = resolution_y / scale
    render.resolution_percentage = scale * 100
    render.pixel_aspect_x = 1.0
    render.pixel_aspect_y = pixel_aspect_ratio

    # set to perspective camera with computed focal length and sensor size
    cam.type = 'PERSP'
    cam.sensor_fit = 'HORIZONTAL'
    cam.lens = f_in_mm
    cam.sensor_width = sensor_size_mm

    return cam


def get_intrinsics(scene, cam):
    """Get the camera intrinsics of a camera

    Note that this code is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate on
        cam (bpy.types.Camera): camera to compute calibration matrix for

    Returns:
        Tuple (fx, fy, cx, cy) of the focal lengths and the camera's principal
        point coordinates.
    """
    if cam.type != 'PERSP':
        raise ValueError('Invalid camera type. Calibration matrix K can be computed only for perspective cameras.')

    render = scene.render

    # get resolution information
    f_in_mm = cam.lens
    scale = scene.render.resolution_percentage / 100
    resolution_y = scale * render.resolution_y
    resolution_x = scale * render.resolution_x

    # extract additional sensor information (size in mm, sensor fit)
    sensor_size_mm = cam.sensor_height if cam.sensor_fit == 'VERTICAL' else cam.sensor_width
    sensor_fit = get_sensor_fit(cam.sensor_fit, render.pixel_aspect_x * resolution_x,
                                                render.pixel_aspect_y * resolution_y)

    # compute pixel size in mm per pixel
    pixel_aspect_ratio = render.pixel_aspect_y / render.pixel_aspect_x
    view_fac_in_px = resolution_x if sensor_fit == 'HORIZONTAL' else resolution_y
    pixel_size_mm_per_px = sensor_size_mm / f_in_mm / view_fac_in_px

    # compute focal length in x and y direction (s_u, s_v)
    s_u = 1.0 / pixel_size_mm_per_px
    s_v = 1.0 / pixel_size_mm_per_px / pixel_aspect_ratio

    # compute intrinsic parameters of K
    u_0 = resolution_x / 2 - cam.shift_x * view_fac_in_px
    v_0 = resolution_y / 2 + cam.shift_y * view_fac_in_px / pixel_aspect_ratio

    # finalize K
    return s_u, s_v, u_0, v_0

