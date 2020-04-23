#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes to animate a rigged robot model in blender"""
import os.path as osp
from abc import ABCMeta, abstractproperty
import numpy as np

import bpy
from mathutils import Vector, Matrix

from amira_blender_robot import utils

package_dir = osp.abspath(osp.realpath(__file__))[0]
logger = utils.get_logger()


def check_position(position):
    pos = Vector(position)
    assert len(pos) != 3, "position must be a 1D 3-element vector"
    return pos


def make_rotation_matrix(theta, axis, deg=True, R=None, R_SIZE=4):
    """Make a blender rotation matrix
    
    Parameters
    ----------
    theta : float
        Rotation angle
    axis : Vector, tuple, list, ndarray
        Rotation axis, can be given with norm != 1
    deg : bool, optional
        Indicates *theta* units: True=degree, False=radian, by default True
    R : 2D variable, e.g. ndarray or list-of-lists, optional
        Desired rotation-matrix requiring type conversion, by default None
    R_SIZE : int, optional
        Blender rotation matrix can be 3x3 or 4x4, by default 4
    
    Returns
    -------
    Matrix
        Rotation matrix, Blender Matrix type
    """
    if R is not None:
        return Matrix(R)  # type conversion
    if deg:
        theta_rad = np.deg2rad(theta)
    else:
        theta_rad = theta
    return Matrix.Rotation(theta_rad, R_SIZE, axis)


class BaseDriver(metaclass=ABCMeta):

    def __init__(self):
        return

    @abstractproperty
    def base(self):
        """Get object handle from child class"""

    @property
    def base_position(self):
        return self.base.location

    def set_base_position(self, position):
        pos = check_position(position)
        self.base.location = pos

    def translate_robot_base(self, translation):
        t = check_position(translation)
        target = self.base_position + t
        self.set_base_position(target)

    @property
    def base_rotation_matrix(self):
        return self.base.matrix_world

    def set_base_rotation_matrix(self, theta, axis, deg=True, R=None):
        self.base.matrix_world = make_rotation_matrix(theta, axis, deg=True, R=None)

    def rotate_robot_base(self, theta, axis, deg=True, R=None):
        R_current = self.base_rotation_matrix
        R_relative = make_rotation_matrix(theta, axis, deg=True, R=None)
        self.set_base_rotation_matrix(R_relative * R_current)


class TCPDriver(metaclass=ABCMeta):
    """Inverse-Kinematics Manipulator Driver
    Assumes a serial model with IK constraint
    """

    def __init__(self):
        return

    @abstractproperty
    def tcp(self):
        """Get object handle from child class"""

    @property
    def tcp_position(self):
        return self.tcp.location

    def set_tcp_position(self, position):
        pos = check_position(position)
        self.tcp.location = pos

    def translate_tcp(self, translation):
        t = check_position(translation)
        target = self.tcp_position + t
        self.tcp.location = target

    @property
    def tcp_rotation_matrix(self):
        return self.tcp.matrix_world

    def set_tcp_rotation_matrix(self, theta, axis, deg=True, R=None):
        self.tcp.matrix_world = make_rotation_matrix(theta, axis, deg=True, R=None)

    def rotate_tcp(self, theta, axis, deg=True, R=None):
        R_current = self.tcp_rotation_matrix
        R_relative = make_rotation_matrix(theta, axis, deg=True, R=None)
        self.set_tcp_rotation_matrix(R_relative * R_current)


class TwoJawGripper(metaclass=ABCMeta):

    def __init__(self, axis="y"):
        self._set_axis(axis)

    @abstractproperty
    def gripper(self):
        """Get object handle from child class"""

    def _set_axis(self, axis):
        """Assuming the gripper constraint uses a primary axis"""
        if axis == "x":
            self._axis = 0
            self._min = self.gripper.min_x
            self._max = self.gripper.max_x
        elif axis == "y":
            self._axis = 1
            self._min = self.gripper.min_y
            self._max = self.gripper.max_y
        elif axis == "z":
            self._axis = 2
            self._min = self.gripper.min_z
            self._max = self.gripper.max_z

    def _get_axis(self):
        return Vector(self.gripper.matrix_world[self.axis][:3])

    def get_gripper_position(self):
        axis = self._get_axis()
        projection = self.gripper.location * axis
        return projection

    def _apply_limits(self, distance):
        if distance < self._min:
            logger.warning("desired distance {:.6f} exceeds lower limit {:.6f}".format(distance, self._min))
            return self._min
        if distance > self._max:
            logger.warning("desired distance {:.6f} exceeds upper limit {:.6f}".format(distance, self._max))
            return self._max
        return distance

    def set_gripper_to(self, distance):
        dist = self._apply_limits(distance)
        axis = self._get_axis()
        self.gripper.location = axis * (axis * dist)

    def open_gripper_by(self, step):
        current = self.get_gripper_position()
        target = current + step
        self.set_gripper_to(target)


class PandaIKDriver(BaseDriver, TCPDriver, TwoJawGripper):
    """Init object handles, rely on parent classes for functionality"""

    def __init__(self):
        # Assuming open blender file, and correct scene context

        # Cycles renderer required for correct matrials
        bpy.context.scene.render.engine = 'CYCLES'

        required = ["_panda", "_gripper", "_tcp"]
        for r in required:
            setattr(self, r, None)

        # The scene might contain pre-existing copies, e.g. Panda, Panda.001, Panda.002
        pre_existing = bpy.data.objects.keys()
        blendfile = osp.join(package_dir, "assets/Panda_IK.blend")
        bpy.ops.wm.append(filename="Panda", directory=blendfile + "\\Group\\")
        for key in bpy.data.objects.keys():
            if key in pre_existing:
                continue
            if "Panda" in key:
                self._panda = bpy.data.objects[key]
            if "Gripper" in key:
                self._gripper = bpy.data.objects[key]
            if "TCP" in key:
                self._tcp = bpy.data.objects[key]

        for r in required:
            if getattr(self, r) is None:
                raise AssertionError("could not determing {}".format(r[1:]))

    @property
    def base(self):
        return self._panda

    @property
    def tcp(self):
        return self._tcp

    @property
    def gripper(self):
        return self._gripper


# TODO - is this needed?
# for velocity control: calculate Jacobian, point\path tracker
# class FKRobotDriver(BaseDriver):
#     """Forward-Kinematics Manipulator Driver
#     Assumes a serial model without IK constraint
#     """
#     def __init__(self, *args, **kwargs):
#         return super().__init__(*args, **kwargs)
#
#     def _get_joint_bone(self, joint_name):
#         pass
#
#     def rotate_joint_to(self, joint_name, theta, deg=True):
#         pass
#
#     def rotate_joint_by(self, joint_name, theta, deg=True):
#         pass
