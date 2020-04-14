#!/usr/bin/env python

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

    Note that this code is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate on
        cam (bpy.types.Camera): camera to compute calibration matrix for
    """
    if cam.type != 'PERSP':
        print(cam.type)
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
    K = Matrix(((s_u, 0, u_0), (0, s_v, v_0), (0, 0, 1)))
    return K


def _set_calibration_matrix_blend(scene, cam, K):
    """Set the calibration matrix K of a camera cam in scene scene, assuming K is of type mathutils.Matrix.

    For more details, see set_calibration_matrix.
    """
    render = scene.render

    # we assume a horizontal sensor with a default height of 1.0, so we only need to set one sensor size
    sensor_size_mm = K[1][1] * K[0][2] / (K[0][0] * K[1][2])
    sensor_fit = 'HORIZONTAL'

    # we assume that the principal point is in the center of the camera
    u_0 = K[0][2]
    v_0 = K[1][2]
    resolution_x = u_0 * 2.0
    resolution_y = v_0 * 2.0
    pixel_aspect_ratio = K[0][0] / K[1][1]

    # compute focal lengths s_u, s_v
    s_u = resolution_x / sensor_size_mm
    s_v = resolution_y / 1.0

    # compute camera focal length in mm
    f_in_mm = K[0][0] / s_u

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


def _set_calibration_matrix_numpy(scene, cam, K):
    """Set the calibration matrix K of a camera cam in scene scene, assuming K is of type np.ndarray.

    For more details, see set_calibration_matrix.
    """
    render = scene.render

    # we assume a horizontal sensor with a default height of 1.0, so we only need to set one sensor size
    sensor_size_mm = K[1, 1] * K[0, 2] / (K[0, 0] * K[1, 2])
    sensor_fit = 'HORIZONTAL'

    # we assume that the principal point is in the center of the camera
    u_0 = K[0, 2]
    v_0 = K[1, 2]
    resolution_x = u_0 * 2.0
    resolution_y = v_0 * 2.0
    pixel_aspect_ratio = K[0, 0] / K[1, 1]

    # compute focal lengths s_u, s_v
    s_u = resolution_x / sensor_size_mm
    s_v = resolution_y / 1.0

    # compute camera focal length in mm
    f_in_mm = K[0, 0] / s_u

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


def set_calibration_matrix(scene, cam, K):
    """Set the calibration matrix K of a camera cam in scene scene.

    Note that the implementation is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://www.rojtberg.net/1601/from-blender-to-opencv-camera-and-back/ and
        3) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        K (np.ndarray or mathutils.Matrix): 3x3 calibration matrix
    """
    if K is None:
        return cam
    if isinstance(K, np.ndarray):
        return _set_calibration_matrix_numpy(scene, cam, K)
    else:
        return _set_calibration_matrix_blend(scene, cam, K)

