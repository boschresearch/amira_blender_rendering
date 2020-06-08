#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file contains a scene manager that sets up a simple environment for
rendering a single object"""

import bpy
import amira_blender_rendering.utils.blender as blnd
from mathutils import Vector


class ThreePointLighting():

    """Setup a scene with classical three point lighting"""

    def __init__(self, *args, **kwargs):
        super(ThreePointLighting, self).__init__()
        self.setup_three_point_lighting()


    def setup_three_point_lighting(self, target = Vector((0.0, 0.0, 0.0))):

        # Key Light
        bpy.ops.object.light_add(type='AREA')
        self.key_light = bpy.context.object
        self.key_light.name = 'Light.Key'
        self.key_light.location = Vector((3.0, 0.0, 1.0))
        self.key_light.data.use_nodes = True
        self.key_light.data.size = 1.0
        self.key_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 13.0
        blnd.look_at(self.key_light, target)

        # Fill Light
        bpy.ops.object.light_add(type='AREA')
        self.fill_light = bpy.context.object
        self.fill_light.name = 'Light.Fill'
        self.fill_light.location = Vector((0.0, -4.0, 2.0))
        self.fill_light.data.use_nodes = True
        self.fill_light.data.size = 3.0
        self.fill_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 10.0
        blnd.look_at(self.fill_light, target)

        # Back Light
        bpy.ops.object.light_add(type='AREA')
        self.back_light = bpy.context.object
        self.back_light.name = 'Light.Back'
        self.back_light.location = Vector((-6.0, 0.0, 0.0))
        self.back_light.data.use_nodes = True
        self.back_light.data.size = 5.0
        self.back_light.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 25.0
        blnd.look_at(self.back_light, target)


# TODO: should become a UnitTest
if __name__ == "__main__":
    mgr = ThreePointLighting()
