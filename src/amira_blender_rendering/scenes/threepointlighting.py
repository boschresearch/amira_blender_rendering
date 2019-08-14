#!/usr/bin/env python

"""This file contains a scene manager that sets up a simple environment for
rendering a single object"""

import bpy
from mathutils import Vector


class ThreePointLighting():

    """Setup a scene with classical three point lighting"""

    def __init__(self):
        super(ThreePointLighting, self).__init__()
        self.setup_three_point_lighting()


    def __look_at(self, obj, target):
        """Rotate an object such that it looks at a target.

        The object's Y axis will point upwards, and the -Z axis towards the
        target. This is the 'correct' rotation for cameras and lights."""
        t = obj.location
        dir = target - t
        quat = dir.to_track_quat('-Z', 'Y')
        obj.rotation_euler = quat.to_euler()


    def setup_three_point_lighting(self, target = Vector((0.0, 0.0, 0.0))):

        # Key Light
        bpy.ops.object.light_add(type='AREA')
        self.key_light = bpy.context.object
        self.key_light.name = 'Light.Key'
        self.key_light.location = Vector((3.0, 0.0, 1.0))
        self.key_light.data.use_nodes = True
        self.key_light.data.size = 1.0
        self.key_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 13.0
        self.__look_at(self.key_light, target)

        # Fill Light
        bpy.ops.object.light_add(type='AREA')
        self.fill_light = bpy.context.object
        self.fill_light.name = 'Light.Fill'
        self.fill_light.location = Vector((0.0, -4.0, 2.0))
        self.fill_light.data.use_nodes = True
        self.fill_light.data.size = 3.0
        self.fill_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 10.0
        self.__look_at(self.fill_light, target)

        # Back Light
        bpy.ops.object.light_add(type='AREA')
        self.back_light = bpy.context.object
        self.back_light.name = 'Light.Back'
        self.back_light.location = Vector((-6.0, 0.0, 0.0))
        self.back_light.data.use_nodes = True
        self.back_light.data.size = 5.0
        self.back_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 25.0
        self.__look_at(self.back_light, target)


# TODO: should become a UnitTest
if __name__ == "__main__":
    mgr = ThreePointLighting()
