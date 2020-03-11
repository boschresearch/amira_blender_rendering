#!/usr/bin/env python

"""This module contains functions for (projective) geometry calculations."""

import bpy
from mathutils import Vector, Euler
from mathutils.bvhtree import BVHTree
import numpy as np


def project_p3d(p: Vector,
                camera: bpy.types.Object = bpy.context.scene.camera,
                render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """Project a point p onto the image plane of a camera. The returned value is
    in normalized device coordiantes. That is, left upper corner is -1,1, right
    bottom lower corner is 1/-1.

    Args:
        p (Vector): 3D vector to project to image plane
        camera (bpy.types.Object): blender camera to use for projection
        render (bpy.types.RenderSettings): render settings used for computation

    Returns:
        2D vector with projected p in normalized device coordiantes
    """

    if camera.type != 'CAMERA':
        raise Exception(f"Object {camera.name} is not a camera")

    if len(p) != 3:
        raise Exception(f"Vector {p} needs to be 3 dimensional")

    # get model-view and projection matrix
    depsgraph = bpy.context.evaluated_depsgraph_get()
    modelview = camera.matrix_world.inverted()
    projection = camera.calc_matrix_camera(
        depsgraph,
        x=render.resolution_x,
        y=render.resolution_y,
        scale_x=render.pixel_aspect_x,
        scale_y=render.pixel_aspect_y)

    # project point (generates homogeneous coordinate)
    p_hom = projection @ modelview @ Vector((p.x, p.y, p.z, 1))

    # normalize to get projected point
    # W = 0 means that we have point that is infinitely far away. Return None
    # in this case
    if p_hom.w == 0.0:
        return None
    else:
        return Vector((p_hom.x / p_hom.w, p_hom.y / p_hom.w))


def p2d_to_pixel_coords(p: Vector, render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """Take a 2D point in normalized device coordiantes to pixel coordinates
    using specified render settings.

    Args:
        p (Vector): 2D vector in normalized device coordinates
        render (bpy.types.RenderSettings): blender render settings to use for
            pixel calculation

    Returns:
        2D vector containing screen space (pixel) coordinate of p
    """

    if len(p) != 2:
        raise Exception(f"Vector {p} needs to be 2 dimensinoal")

    return Vector(((render.resolution_x - 1) * (p.x + 1.0) / +2.0,
                   (render.resolution_y - 1) * (p.y - 1.0) / -2.0))


def get_relative_rotation(obj1: bpy.types.Object, obj2: bpy.types.Object = bpy.context.scene.camera) -> Euler:

    """Get the relative rotation between two objects in terms of the second
    object's coordinate system. Note that the second object will be default
    initialized to the scene's camera.

    Returns:
        Euler angles given in radians
    """

    obj1_m = obj1.rotation_euler.to_matrix()
    obj2_m = obj2.rotation_euler.to_matrix()
    rel_rotation_m = (obj1_m.inverted() @ obj2_m)
    rel_rotation_e = rel_rotation_m.to_euler()
    return rel_rotation_e


def get_relative_translation(obj1: bpy.types.Object, obj2: bpy.types.Object = bpy.context.scene.camera) -> Vector:
    """Get the relative translation between two objects in terms of the second
    object's coordinate system. Note that the second object will be default
    initialized to the scene's camera.

    Args:
        obj1 (bpy.types.Object): first object
        obj2 (bpy.types.Object): second object, relative to which the
            translation will be computed.

    Returns:
        3D Vector with relative translation (in OpenGL coordinates)
    """

    # get vector in world coordinats and rotate into object cordinates
    v = obj1.location - obj2.location
    rot = obj2.rotation_euler.to_matrix()
    return rot.inverted() @ v


def get_relative_transform(obj1: bpy.types.Object, obj2: bpy.types.Object = bpy.context.scene.camera):
    """Get the relative transform between obj1 and obj2 in obj2's coordinate
    frame.

    Args:
        obj1 (bpy.types.Object): first object
        obj2 (bpy.types.Object): second object, relative to which the
            transform will be computed.

    Returns:
        tuple containing the translation and rotation between obj1 and obj2
        (relative to obj2)

    """

    t = get_relative_translation(obj1, obj2)
    r = get_relative_rotation(obj1, obj2)
    return t, r


def test_visibility(obj, cam, width, height):
    # Test if object is still visible. That is, none of the vertices
    # should lie outside the visible pixel-space
    vs = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    ps = [project_p3d(v, cam) for v in vs]
    # Test if we encountered a "point at infinity"
    if None in ps:
        return False
    else:
        pxs = [p2d_to_pixel_coords(p) for p in ps]
        oks = [px[0] >= 0 and px[0] < width and px[1] >= 0 and px[1] < height for px in pxs]
        return all(oks)


def _get_bvh(obj):
    mat = obj.matrix_world
    vs = [mat @ v.co for v in obj.data.vertices]
    ps = [p.vertices for p in obj.data.polygons]
    return BVHTree.FromPolygons(vs, ps)


def test_intersection(obj1, obj2):
    """Test if two objects intersect each other

    Returns true if objects intersect, false if not.
    """
    bvh1 = _get_bvh(obj1)
    bvh2 = _get_bvh(obj2)
    if bvh1.overlap(bvh2):
        return True
    else:
        return False


def get_world_to_object_tranform(cam2obj_pose: dict, camera: bpy.types.Object = bpy.context.scene.camera):
    """
    Transform a pose {'R', 't'} expressed in camera coordinates to world coordinates

    Args:
        cam2obj_pose(dict): {
            'R'(np.array(3)) : rotation matrix from camera to obj
            't'(np.array(3,) : translation vector from camera to obh
        }
        camera(bpq.types.Object): scene camera

    Returns:
        {'R','t'} where
        R(np.array(3)): rotation matrix from world frame to object
        t(np.array(3,)): translation vector from world frame to object
    """
    # TODO: this could probably be done using Matrix and Vectors from mathutils

    # camera to object transformation
    M_c2o = np.eye(4)
    M_c2o[:3, :3] = cam2obj_pose['R']
    M_c2o[:3, 3] = cam2obj_pose['t']

    # world to camera transformation
    M_w2c = np.eye(4)
    M_w2c[:3, :3] = camera.rotation_euler.to_matrix()
    M_w2c[:3, 3] = camera.location

    # world to object
    M_w2o = M_w2c.dot(M_c2o)

    # extract pose
    R = M_w2o[:3, :3]
    t = M_w2o[:3, 3]

    # pack into dictionary to maintain input format and return
    return {'R': R, 't': t}


def gl2cv(R, t):
    """Convert transform from OpenGL to OpenCV
    
    Args:
        R(np.array(3,3): rotation matrix
        t(np.array(3,): translation vector
    Returns:
        R_cv
        t_cv
    """
    M_gl = np.eye(4)
    M_gl[:3, :3] = R
    M_gl[:3, 3] = t
    Ccv_Cgl = np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    return Ccv_Cgl @ M_gl
