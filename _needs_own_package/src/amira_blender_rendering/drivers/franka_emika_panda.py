#!/usr/bin/env python

"""
Classes to animate a Franka Emika Panda robot model in blender.
"""

import os.path as osp
import numpy as np

import bpy
from mathutils import Vector, Matrix, Quaternion

import amira_blender_rendering.utils.io as ioutils
import amira_blender_rendering.utils.blender as blnd
from amria_blender_rendering.drivers.rigidbody import RigidBody
from amira_blender_rendering.drivers.grippers import TwoJawGripper
from amira_blender_rendering.utils.logging import get_logger

logger = get_logger()

class PandaDriverParent():
    """Contains shared functionality, cannot drive the robot"""

    def __init__(self):
        self.n_dof = 7  # excluding gripper

        # Assuming open blender file, and correct scene context
        if bpy.context.scene.render.engine != "CYCLES":
            logger.warning("Switching to Cycles-Render, required for Panda Turbo-Squid model")
            bpy.context.scene.render.engine = "CYCLES"

        for obj in ["base", "tcp", "gripper"]:
            setattr(self, obj, None)

        # The scene might contain pre-existing copies, e.g. Panda, Panda.001, Panda.002
        pre_existing = bpy.data.objects.keys()
        pkg = utils.get_my_dir(__file__)

        blendfile = ioutils.expandpath(f"$AMIRA_BLENDER_RENDERING_ASSETS/Panda_IK_280.blend")
        bpy.ops.wm.append(filename="Panda", directory=blendfile + "\\Collection\\")


        # TODO : might need to remove duplicate material names
        for key in bpy.data.objects.keys():
            if key in pre_existing:
                continue
            if "Panda" in key:
                self.base = RigidBody(bpy.data.objects[key])
            if "Gripper" in key:
                self.gripper = TwoJawGripper(bpy.data.objects[key])
            if "TCP" in key:
                tcp = bpy.data.objects[key]

        for req in ["base", "gripper"]:
            if getattr(self, req) is None:
                raise AssertionError("could not determine {}".format(req))

        return tcp

    def delete(self):
        if self.gripper:
            blnd.delete_object(self.gripper._obj.name)
        if self.tcp:
            blnd.delete_object(self.tcp._obj.name)
        if self.base:
            children = [c.name for c in self.base._obj.children]
            for c in children:
                blnd.delete_object(c)
            blnd.delete_object(self.base._obj.name)


class PandaIKDriver(PandaDriverParent):
    """IK is simpler to use, and good enough for Wrist-Camera rendering"""

    def __init__(self):
        tcp = PandaDriverParent.__init__(self)
        if tcp:
            self.tcp = RigidBody(tcp)
        else:
            raise AssertionError("could not determine TCP")

    def randomize_tcp(self, xlim=None, ylim=None, zlim=(0.4, 10)):
        """Using coarse approximaiton of workspace"""
        # TODO: set better limits, this is a bit too crazy
        EPS = 1e-4
        R_XY = 0.85
        R_Z_UP = 1.1
        R_Z_DOWN = 0.2
        MIN_R_XY = 0.25

        r_prop = np.random.rand(1)
        theta = np.random.rand(1) * np.deg2rad(360.0)
        phi = np.random.rand(1) * np.deg2rad(90.0)

        if zlim[0] >= 0:
            denom = ((np.sin(phi) / R_XY)**2 + (np.cos(phi) / R_Z_UP)**2)
            r2_max = 1.0 / denom
        else:
            phi *= 2.0
            denom = ((np.sin(phi) / R_XY)**2 + (np.cos(phi) / R_Z_DOWN)**2)
            r2_max = 1.0 / denom
        r = r_prop * np.sqrt(r2_max)

        xyz = [
            r * np.cos(theta) * np.sin(phi),
            r * np.sin(theta) * np.sin(phi),
            r * np.cos(phi),
        ]

        # Applying cartesian limits
        if xlim is not None:
            xyz[0] = min(xlim[1], max(xlim[0], xyz[0]))
        if ylim is not None:
            xyz[1] = min(ylim[1], max(ylim[0], xyz[1]))
        if zlim is not None:
            xyz[2] = min(zlim[1], max(zlim[0], xyz[2]))

        # Avoiding self-colision [coarse]
        r_xy = np.sqrt(xyz[0]**2 + xyz[1]**2)
        ratio = MIN_R_XY / (r_xy + EPS)
        if ratio > 1.0:
            xyz[0] *= ratio
            xyz[1] *= ratio

        # Adding base position
        for k in range(3):
            xyz[k] += self.base.position[k]

        self.tcp.set_position(xyz)

        theta_x = -0.5 * np.pi * np.random.rand(1)
        theta_z = theta - (0.5 * np.pi)

        # FIXME: think of better implementation, in respect to encapsulation
        current_mode = self.tcp._obj.rotation_mode
        self.tcp._obj.rotation_mode = "XYZ"
        self.tcp._obj.rotation_euler.x = theta_x
        self.tcp._obj.rotation_euler.z = theta_z
        self.tcp._obj.rotation_mode = current_mode


class PandaFKDriver(PandaDriverParent):
    """FK enables joint position control

    Each joint has 1 legal DOF: Y rotation
    """

    def __init__(self):
        # See: https://frankaemika.github.io/docs/control_parameters.html
        self._joint_limits = {
            "Axis-1": dict(min=-2.8973, max=2.8973),
            "Axis-2": dict(min=-1.7628, max=1.7628),
            "Axis-3": dict(min=-2.8973, max=2.8973),
            "Axis-4": dict(min=-3.0718, max=-0.0698),  # TODO: check for offset
            "Axis-5": dict(min=-2.8973, max=2.8973),
            "Axis-6": dict(min=-0.0175, max=3.7525),
            "Axis-7": dict(min=-2.8973, max=2.8973),
        }

        tcp = PandaDriverParent.__init__(self)
        self.pose_bones = self.base._obj.pose.bones
        wrist = self.pose_bones["Axis-7"]
        ik_constraint = wrist.constraints["IK"]
        wrist.constraints.remove(ik_constraint)
        if tcp:
            blnd.delete_object(tcp.name)

    def _theta_to_rad(self, theta, deg):
        if deg:
            return np.deg2rad(theta)
        else:
            return theta

    def _check_joint_name(self, joint_name):

        if isinstance(joint_name, str):
            if joint_name in self.pose_bones.keys():
                return joint_name
            raise AssertionError("joint_name not found in pose bones: {}".format(joint_name))

        if isinstance(joint_name, int):
            _id = joint_name
            if 0 <= _id < self.n_dof:
                return self.pose_bones[_id].name
            else:
                raise AssertionError("Bone ID must be int in 0-{} range, got: {}".format(self.n_dof - 1, _id))

        raise TypeError("expecting string or int, not: {}, {}".format(joint_name, type(joint_name)))

    def _apply_joint_limits(self, joint_name, theta):
        joint_name = self._check_joint_name(joint_name)
        _min = self._joint_limits[joint_name]["min"]
        _max = self._joint_limits[joint_name]["max"]
        valid_theta = min(_max, max(_min, theta))
        if theta != valid_theta:
            msg = "{} angle must be in range {} - {}, requested: {}".format(joint_name, _min, _max, theta)
            logger.warning(msg)
        return valid_theta

    def _get_pose_bone(self, joint_name):
        joint_name = self._check_joint_name(joint_name)
        return self.pose_bones[joint_name]

    def _get_quaternion(self, joint_name):
        return self._get_pose_bone(joint_name).rotation_quaternion

    def get_joint_angle(self, joint_name, deg=True):
        q = self._get_quaternion(joint_name)
        theta = np.arctan2(np.linalg.norm(q[1:]), q[0])
        if deg:
            theta = np.rad2deg(theta)
        return theta

    def set_joint_angle(self, joint_name, theta, deg=True):
        bone = self._get_pose_bone(joint_name)

        current_rotation_mode, bone.rotation_mode = bone.rotation_mode, 'QUATERNION'

        theta_rad = self._theta_to_rad(theta, deg)
        theta_rad = self._apply_joint_limits(joint_name, theta_rad)

        half_theta = 0.5 * theta_rad
        q = Quaternion((np.cos(half_theta), .0, np.sin(half_theta), .0))
        bone.rotation_quaternion = q

        bone.rotation_mode = current_rotation_mode

    def increment_joint_angle(self, joint_name, delta_theta, deg=True):
        theta_current_rad = self.get_joint_angle(joint_name, deg=False)
        delta_theta_rad = self._theta_to_rad(delta_theta, deg)
        target_theta_rad = theta_current_rad + delta_theta_rad
        self.set_joint_angle(joint_name, target_theta_rad, deg=False)
