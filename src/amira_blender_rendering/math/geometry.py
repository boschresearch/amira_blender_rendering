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

"""This module contains functions for (projective) geometry.

The file also contains functions that are commonly used in this domain, such as
rotation matrix computations, conversions between OpenGL and OpenCV, etc.
"""

import bpy
from math import pi
from mathutils import Vector, Euler
from mathutils.bvhtree import BVHTree
from amira_blender_rendering.utils.logging import get_logger
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
    obj1_m = obj1.matrix_world.to_3x3().normalized()
    obj2_m = obj2.matrix_world.to_3x3().normalized()
    rel_rotation = (obj2_m.inverted() @ obj1_m).to_euler()
    return rel_rotation


def get_relative_rotation_to_cam_deg(obj, cam, zeroing=Vector((90, 0, 0))):
    """Get the relative rotation between an object and a camera in the camera's
    frame of reference.

    For more details, see get_relative_rotation_to_cam_rad.

    Args:
        obj: object to compute relative rotation for
        cam: camera to used
        zeroing: camera zeroing angles (in degrees)

    Returns:
        Relative rotation between object and camera in the coordinate frame of
        the camera.
    """
    return get_relative_rotation_to_cam_rad(obj, cam, zeroing * pi / 180)


def get_relative_rotation_to_cam_rad(obj, cam, zeroing=Vector((pi/2, 0, 0))):
    """Get the relative rotation between an object and a camera in the camera's
    frame of reference.

    This function allows to specify a certain 'zeroing' rotation.

    A default camera in blender with 0 rotation applied to its transform looks
    along the -Z direction. Blender's modelling viewport, however, assumes that
    the surface plane is spanned by X and Y, where X indicates left/right. This
    can be observed by putting the modelling viewport into the front viewpoint
    (Numpad 1). Then, the viewport looks along the Y direction.

    As a consequence, the relative rotation between a camera image and an object
    is only 0 when the camera would look onto the top of the object. Note that
    this is rather unintuitive, as most people would expect that the relative
    rotation is 0 when the camera looks at the front of an object.

    Args:
        obj: object to compute relative rotation for
        cam: camera to used
        zeroing: camera zeroing angles (in radians)

    Returns:
        Relative rotation between object and camera in the coordinate frame of
        the camera.
    """
    obj_m = obj.matrix_world.to_3x3().normalized()
    cam_m = cam.matrix_world.to_3x3().normalized()
    rel_rotation = cam_m.inverted() @ obj_m
    cam_rot = Euler([zeroing[0], zeroing[1], zeroing[2]]).to_matrix()
    return (cam_rot @ rel_rotation).to_euler()


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
    v = obj1.matrix_world.to_translation() - obj2.matrix_world.to_translation()
    rot = obj2.matrix_world.to_3x3().normalized()
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


def test_visibility(obj, cam, width, height, require_all=True):
    """Test if an object is visible from a camera by projecting the bounding box
    of the object and testing if the vertices are visible from the camera or not.

    Note that this does not test for occlusions!

    Args:
        obj : Object to test visibility for
        cam : Camera object
        width : Viewport width
        height : Viewport height
        require_all: test all (True) or at least one (False) bounding box vertex

    Returns:
        True, if object is visible, false if not.
    """
    render = bpy.context.scene.render
    # Test if object is still visible. That is, none of the vertices
    # should lie outside the visible pixel-space
    vs = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    ps = [project_p3d(v, cam, render=render) for v in vs]
    # Test if we encountered a "point at infinity"
    if None in ps:
        return False
    else:
        pxs = [p2d_to_pixel_coords(p, render=render) for p in ps]
        oks = [px[0] >= 0 and px[0] < width and px[1] >= 0 and px[1] < height for px in pxs]
        return all(oks) if require_all else any(oks)


def test_occlusion(scene, layer, cam, obj, width, height, require_all=True, origin_offset=0.01):
    """Test if an object is visible or occluded by another object by checking its vertices.
    Note that this also tests if an object is visible.

    Args:
        scene: the scene for which to test
        layer: view layer to use for ray casting, e.g. scene.view_layers['View Layer']
        cam: camera to evaluate
        obj: object to evaluate
        width: scene render width, e.g. scene.render.resolution_x
        height: scene render height, e.g. scene.render.resolution_y
        require_all: test all vertices of the object for visibility and
            occlusion or not
        origin_offset: for ray-casting, add this offset along the ray to the
            origin. This helps to prevent numerical issues when a mesh is exactly at
            cam's location.

    Returns:
        True if an object is not visible or occluded, False if the object is
        visible and not occluded. Note that the returned value depends on
        argument require_all. Specifically, if require_all is set to False, then
        this function returns False if one of its vertices is visible and not
        occluded, and True if none of the vertex is visible or all are occluded.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    render = bpy.context.scene.render

    # get mesh, evaluated after simulations, and camera origin from the camera's
    # world matrix
    mesh = obj.evaluated_get(dg).to_mesh()
    origin = cam.matrix_world.to_translation()
    vs = [obj.matrix_world @ v.co for v in mesh.vertices]
    obj.to_mesh_clear()

    # compute projected vertices
    ps = [project_p3d(v, cam, render=render) for v in vs]
    if None in ps:
        return True

    # compute pixel coordinates for each vertex
    pxs = [p2d_to_pixel_coords(p, render=render) for p in ps]

    # keep track of what is going on
    vs_visible = [px[0] >= 0 and px[0] < width and px[1] >= 0 and px[1] < height for px in pxs]
    vs_occluded = [False] * len(vs)

    for i, v in enumerate(vs):
        # compute direction of ray from camera to this vertex and perform cast
        direction = v - origin
        direction.normalize()
        # 'repair' the origin by walking along the ray by a little offset
        local_origin = origin + origin_offset * direction
        hit_record = scene.ray_cast(layer, local_origin, direction)
        hit = hit_record[0]
        hit_location = hit_record[1]
        hit_obj = hit_record[4]

        # assume hit
        if hit and not (hit_obj.type == 'CAMERA') and not (hit_obj == obj):
            vs_occluded[i] = True

    if require_all:
        return not (all(vs_visible) and all([not oc for oc in vs_occluded]))
    else:
        for i in range(len(vs_visible)):
            if vs_visible[i] and not vs_occluded[i]:
                return False
        return True


def _get_bvh(obj):
    """Get the BVH for an object

    Args:
        obj (variant): object to get the BVH for

    Returns:
        BVH for obj
    """
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


def get_world_to_object_transform(cam2obj_pose: dict, camera: bpy.types.Object = bpy.context.scene.camera):
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
    M_w2c[:3, :3] = camera.matrix_world.to_3x3().normalized()
    M_w2c[:3, 3] = camera.matrix_world.to_translation()

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
    Cgl_W = Ccv_Cgl @ M_gl
    # return as R and t, as expected by the docstring
    return Cgl_W[:3, :3], Cgl_W[:3, 3]


def euler_x_to_matrix(angle):
    """Get rotation matrix from euler angle rotation around X."""
    return np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]])


def euler_y_to_matrix(angle):
    """Get rotation matrix from euler angle rotation around Y."""
    return np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]])


def euler_z_to_matrix(angle):
    """Get rotation matrix from euler angle rotation around Z."""
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]])


def rotation_matrix(alpha, axis, homogeneous=False):
    """Euler rotation matrices

    Args:
        alpha (float): angle in radians
        axis (str): x/y/z
        homogeneous (bool): output homogeneous coordinates

    Returns:
        rotation matrix

    """

    # make sure axis is lower case
    axis = axis.lower()

    if axis == 'x':
        # rotation around x
        rot = euler_x_to_matrix(alpha)
    elif axis == 'y':
        # rotation around y
        rot = euler_y_to_matrix(alpha)
    elif axis == 'z':
        # rotation around z
        rot = euler_z_to_matrix(alpha)
    else:
        get_logger().error('Axis needs to be x/y/z!')
        raise ValueError

    # create homogeneous matrix
    if homogeneous is True:
        h = np.eye(4)
        h[:3, :3] = rot
        return h
    else:
        return rot


# the two following method have been implemented in the amira_lfd pipeline
def rotation_matrix_to_quaternion(rot_mat, isprecise=False):
    """
    Computes the quaternion (with convention WXYZ) out of a given rotation matrix
    Inverse funtion of quaternion_to_rotation_matrix

    Parameters
    ----------
    :param rot_mat:  np.array of shape (3, 3)

    Returns
    -------
    :return q: np.array of shape (4,), quaternion (WXYZ) corresponding to the rotation matrix rot_mat
    
    NOTE: the implementation comes from a mixture of codes. Inspiration is taken from Wikipedia and
        
        Homogeneous Transformation Matrices and Quaternions library
        :Author:
            `Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/>`_
    """
    if isprecise:
        trace = max(np.trace(rot_mat), -1.0)
        qs = min(np.sqrt(trace + 1) / 2.0, 1.0)
        kx = rot_mat[2, 1] - rot_mat[1, 2]  # Oz - Ay
        ky = rot_mat[0, 2] - rot_mat[2, 0]  # Ax - Nz
        kz = rot_mat[1, 0] - rot_mat[0, 1]  # Ny - Ox
        if (rot_mat[0, 0] >= rot_mat[1, 1]) and (rot_mat[0, 0] >= rot_mat[2, 2]):
            kx1 = rot_mat[0, 0] - rot_mat[1, 1] - rot_mat[2, 2] + 1  # Nx - Oy - Az + 1
            ky1 = rot_mat[1, 0] + rot_mat[0, 1]  # Ny + Ox
            kz1 = rot_mat[2, 0] + rot_mat[0, 2]  # Nz + Ax
            add = (kx >= 0)
        elif rot_mat[1, 1] >= rot_mat[2, 2]:
            kx1 = rot_mat[1, 0] + rot_mat[0, 1]  # Ny + Ox
            ky1 = rot_mat[1, 1] - rot_mat[0, 0] - rot_mat[2, 2] + 1  # Oy - Nx - Az + 1
            kz1 = rot_mat[2, 1] + rot_mat[1, 2]  # Oz + Ay
            add = (ky >= 0)
        else:
            kx1 = rot_mat[2, 0] + rot_mat[0, 2]  # Nz + Ax
            ky1 = rot_mat[2, 1] + rot_mat[1, 2]  # Oz + Ay
            kz1 = rot_mat[2, 2] - rot_mat[0, 0] - rot_mat[1, 1] + 1  # Az - Nx - Oy + 1
            add = (kz >= 0)
        if add:
            kx = kx + kx1
            ky = ky + ky1
            kz = kz + kz1
        else:
            kx = kx - kx1
            ky = ky - ky1
            kz = kz - kz1
        nm = np.linalg.norm(np.array([kx, ky, kz]))
        if nm == 0:
            q = np.array([1., 0., 0., 0.])
        else:
            s = np.sqrt(1 - qs**2) / nm
            qv = s * np.array([kx, ky, kz])
            q = np.append(qs, qv)
    else:
        m00 = rot_mat[0, 0]
        m01 = rot_mat[0, 1]
        m02 = rot_mat[0, 2]
        m10 = rot_mat[1, 0]
        m11 = rot_mat[1, 1]
        m12 = rot_mat[1, 2]
        m20 = rot_mat[2, 0]
        m21 = rot_mat[2, 1]
        m22 = rot_mat[2, 2]
        # symmetric matrix K
        K = np.array([[m00 - m11 - m22, 0.0, 0.0, 0.0], [m01 + m10, m11 - m00 - m22, 0.0, 0.0],
                      [m02 + m20, m12 + m21, m22 - m00 - m11, 0.0],
                      [m21 - m12, m02 - m20, m10 - m01, m00 + m11 + m22]])
        K /= 3.0
        # quaternion is eigenvector of K that corresponds to largest eigenvalue
        w, V = np.linalg.eigh(K)
        q = V[[3, 0, 1, 2], np.argmax(w)]

    if q[0] < 0.0:
        np.negative(q, q)
    return q
