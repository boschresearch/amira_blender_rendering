#!/usr/bin/env python

import bpy
from mathutils import Vector


def opencv_to_blender(width, height, K, cam):
    """Convert the intrinsic camera from OpenCV to blender's format

    Args:
        K (np.array): 3x3 intrinsic camera calibration matrix
    """

    # TODO: this function does not appear to work correctly. A test with small
    #       output sizes (640x480) showed that the function actually shifted the
    #       camera in a weird way. Until this is fixed, the function ignores all
    #       inputs and simply returns the cam argument.
    if True:
        return cam

    # extract relevant values from K :
    #
    #           fx  s cx
    #       K =  0 fy cy
    #            0  0  1
    #
    fx = K[0, 0]
    fy = K[1, 1]
    cx = K[0, 2]
    cy = K[1, 2]

    cam.data.shift_x = -(cx / width - 0.5)
    cam.data.shift_y =  (cy - 0.5 * height) / width

    sensor_width_in_mm = cam.data.sensor_width
    cam.data.lens = fx / width * sensor_width_in_mm

    scene = bpy.context.scene
    pixel_aspect = fy / fx
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = pixel_aspect

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

