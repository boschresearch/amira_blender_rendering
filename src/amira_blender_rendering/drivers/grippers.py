#!/usr/bin/env python

"""
Classes to simulate various grippers in blender.
"""

import bpy
from mathutils import Vector, Matrix, Quaternion
from amira_blender_rendering.utils.logging import get_logger

logger = get_logger()

# TODO : add tests
class Gripper():  # use a AnimatedObject base class for TwoJawGripper and RigidBody ?

    def __init__(self, obj_handle):
        self._obj = obj_handle

    def keyframe_insert(self, data_path, frame=None):
        if frame is None:
            frame = bpy.context.scene.frame_current
        self._obj.keyframe_insert(data_path=data_path, frame=(frame))


class TwoJawGripper(Gripper):

    def __init__(self, obj_handle, axis="y"):
        super(TwoJawGripper, self).__init__(obj_handle)
        self._constraint = obj_handle.constraints['Limit Location']
        self._set_axis(axis)

    def _set_axis(self, axis):
        """Assuming the gripper constraint uses a primary axis"""
        if axis == "x":
            self._axis = 0
            self._min = self._constraint.min_x
            self._max = self._constraint.max_x
        elif axis == "y":
            self._axis = 1
            self._min = self._constraint.min_y
            self._max = self._constraint.max_y
        elif axis == "z":
            self._axis = 2
            self._min = self._constraint.min_z
            self._max = self._constraint.max_z

    def _get_axis(self):
        return Vector(self.matrix_world[self._axis][:3])

    def get_openning(self):
        return self._obj.location[self._axis]

    def _apply_limits(self, distance):
        if distance < self._min:
            logger.warning("desired distance {:.6f} exceeds lower limit {:.6f}".format(distance, self._min))
            return self._min
        if distance > self._max:
            logger.warning("desired distance {:.6f} exceeds upper limit {:.6f}".format(distance, self._max))
            return self._max
        return distance

    def set_to(self, distance):
        dist = self._apply_limits(distance)
        self._obj.location[self._axis] = dist

    def open_by(self, step):
        current = self.get_openning()
        target = current + step
        self.set_to(target)

