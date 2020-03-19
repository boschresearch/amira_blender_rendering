#!/usr/bin/env python

import bpy
from mathutils import Vector


def opencv_to_blender(K, cam, scale = 1.0):
    """Convert the intrinsic camera from OpenCV to blender's format

    Args:
        K (np.array): 3x3 intrinsic camera calibration matrix

    """
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

