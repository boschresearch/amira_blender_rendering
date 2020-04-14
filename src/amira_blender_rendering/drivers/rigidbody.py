#!/usr/bin/env python

"""
Rigid Body base class that can be used to simulate rigid body robots in blender.
"""

import bpy
from mathutils import Vector, Matrix, Quaternion
import numpy as np

class RigidBody():

    def __init__(self, obj_handle):
        self._obj = obj_handle

    def __getattr__(self, attr):
        """Provides acces to native blender functionality
        __getattribute__ is called before __getattr__, so RigidBody attributes will not get here
        """
        try:
            return getattr(self._obj, attr)
        except AttributeError:
            raise AttributeError(attr)

    @property
    def position(self):
        return self._obj.location

    @property
    def rotation_matrix(self):
        return Matrix(np.array(self.matrix_world)[:3, :3])

    # TODO : add test
    def keyframe_insert(self, data_path, frame=None):
        if frame is None:
            frame = bpy.context.scene.frame_current
        self._obj.keyframe_insert(data_path=data_path, frame=(frame))

    def check_position(self, position):
        pos = Vector(position)
        assert len(pos) == 3, "position must be a 1D 3-element vector"
        return pos

    def set_position(self, position):
        pos = self.check_position(position)
        self._obj.location = pos

    def translate(self, translation):
        t = self.check_position(translation)
        target = self._obj.location + t
        self.set_position(target)

    def make_rotation_matrix(self, theta, axis, deg=True, R_SIZE=4):
        """Make a blender rotation matrix

        Parameters
        ----------
        theta : float
            Rotation angle
        axis : Vector, tuple, list, ndarray
            Rotation axis, can be given with norm != 1
        deg : bool, optional
            Indicates *theta* units: True=degree, False=radian, by default True
        R_SIZE : int, optional
            Blender rotation matrix can be 3x3 or 4x4, by default 4

        Returns
        -------
        Matrix
            Rotation matrix, Blender Matrix type
        """
        if deg:
            theta_rad = np.deg2rad(theta)
        else:
            theta_rad = theta
        return Matrix.Rotation(theta_rad, R_SIZE, axis)

    def set_rotation_matrix(self, theta, axis, deg=True):
        R = self.make_rotation_matrix(theta, axis, deg=deg)
        self.set_rotation_matrix_to_R(R)

    def set_rotation_matrix_to_R(self, R):
        if len(R) == 4:
            self._obj.matrix_world = R
        elif len(R) == 3:
            H = self.matrix_world
            for k in range(3):
                H[k][:3] = R[k]
            self._obj.matrix_world = H

    def rotate(self, theta, axis, deg=True):
        R_relative = self.make_rotation_matrix(theta, axis, deg=deg)
        self.rotate_by_R(R_relative)

    def rotate_by_R(self, R):
        # FIXME: so far this was only tested with R 4x4 (H)
        # should work for both R and H, need to check dimensions
        R_current = self.matrix_world
        R_final = R @ R_current
        self.set_rotation_matrix_to_R(R_final)

