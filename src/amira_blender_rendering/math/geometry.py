#!/usr/bin/env python

"""This module contains functions for (projective) geometry.

The file also contains functions that are commonly used in this domain, such as
rotation matrix computations, conversions between OpenGL and OpenCV, etc.
"""

import bpy
from math import pi
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
    obj_m = obj.rotation_euler.to_matrix()
    cam_m = cam.rotation_euler.to_matrix()
    rel_rotation_m = obj_m.inverted() @ cam_m
    cam_rot = Euler([zeroing[0], zeroing[1], zeroing[2]]).to_matrix()
    return (cam_rot.inverted() @ rel_rotation_m).to_euler()


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
    """Test if an object is visible from a camera

    Args:
        obj : Object to test visibility for
        cam : Camera object
        width : Viewport width
        height : Viewport height

    Returns:
        True, if object is visible, false if not.
    """
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
        logger.error('Axis needs to be x/y/z!')
        raise ValueError

    # create homogeneous matrix
    if homogeneous is True:
        h = np.eye(4)
        h[:3, :3] = rot
        return h
    else:
        return rot


# the two following method have been implemented in the amira_lfd pipeline
def rotation_matrix_to_quaternion(rot_mat):
    """
    Computes the quaternion (with convention WXYZ) out of a given rotation matrix
    Inverse funtion of quaternion_to_rotation_matrix

    Parameters
    ----------
    :param rot_mat:  np.array of shape (3, 3)

    Returns
    -------
    :return q: np.array of shape (4,), quaternion (WXYZ) corresponding to the rotation matrix rot_mat
    """
    qs = min(np.sqrt(np.trace(rot_mat) + 1) / 2.0, 1.0)
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
    return q

