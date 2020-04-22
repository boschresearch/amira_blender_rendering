#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rotation math"""
import numpy as np
import mathutils
from amira_blender_robot import utils

logger = utils.get_logger()

X_AXIS = np.array((1, 0, 0))
Y_AXIS = np.array((0, 1, 0))
Z_AXIS = np.array((0, 0, 1))


# TODO: consider supporting\using bpy.mathutils types: Vector, Matrix, Quaternion
class VariableChecker():

    def __init__(self):
        return

    def is_scalar(var, _raise=False):
        decision = isinstance(var, (int, float))
        if not decision and _raise:
            raise TypeError("must be a scalar value, not {}".format(type(var)))
        return decision

    def check_theta(self, theta, units="deg"):
        self.is_scalar(theta, _raise=True)
        if units == "deg":
            theta_rad = np.deg2rad(theta)
        elif units == "rad":
            theta_rad = theta
        else:
            raise ValueError("unsupported unit type: {}".format(units))
        return theta_rad

    def is_numeric_container(self, var):
        try:
            np.all(np.isfinite(var))
        except TypeError as err:
            logger.error("Expecting a list or tuple of numbers")
            logger.error(print(err))
            return False
        return True

    def is_vector(self, var):
        if isinstance(var, mathutils.Vector):
            return True
        if isinstance(var, np.ndarray):
            return self.is_numpy_vector(var)
        if self.is_numeric_container(var):
            return self.is_numpy_vector(np.array(var))
        return False

    def is_numpy_vector(self, var: np.ndarray, _raise=False):
        if not isinstance(var, np.ndarray):
            if _raise:
                raise TypeError("Only supporting ndarray")
            else:
                return False
        if var.ndim == 1:
            return True
        count = 0
        for s in var.shape:
            if s > 1:
                count += 1
            if count > 1:
                return False
        return True

    def normalize_vector(self, var):
        if not self.is_vector(var):
            raise ValueError("Expecting a 1D ndarray")
        if not isinstance(var, (np.ndarray, mathutils.Vector)):
            var = np.array(var)
        return var / np.linalg.norm(var)

    def is_3_elements_vector(self, var):
        if not self.is_vector(var):
            return False
        if isinstance(var, mathutils.Vector):
            return len(var) == 3
        u = np.array(var).flatten()
        if self.is_numeric_container(u):
            return u.shape == (3,)
        return False

    def check_axis(self, axis):
        if not self.is_vector(axis):
            raise TypeError("not a vector")
        if not self.is_3_elements(axis):
            raise AssertionError("axis needs to be a 1D 3-element variable")
        return self.normalize_vector(axis)


class RotationMatrix():

    def __init__(self):
        self._checker = VariableChecker()

    def R_theta_axis(self, theta, axis, units="deg"):
        """See wikipedia `Rotation Matrix <https://en.wikipedia.org/wiki/Rotation_matrix>`_"""
        theta_rad = self._checker.check_theta(theta, units=units)
        cos_t = np.cos(theta_rad)
        sin_t = np.sin(theta_rad)

        u = self._checker.check_axis(axis)

        u_cross = np.zeros((3, 3))
        u_cross[0, 1] = -u[2]
        u_cross[0, 2] = u[1]
        u_cross[1, 2] = -u[0]
        u_cross[1, 0] = u[2]
        u_cross[2, 0] = -u[1]
        u_cross[2, 1] = u[0]

        u_outer = np.kron(np.expand_dims(u, 1), u)

        R = cos_t * np.eye(3) + sin_t * u_cross + (1.0 - cos_t) * u_outer
        return R

    def Rx(self, theta, units="deg"):
        return self.R_theta_axis(theta, X_AXIS, units=units)

    def Ry(self, theta, units="deg"):
        return self.R_theta_axis(theta, Y_AXIS, units=units)

    def Rz(self, theta, units="deg"):
        return self.R_theta_axis(theta, Z_AXIS, units=units)
