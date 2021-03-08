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

import bpy
from mathutils import Vector
from amira_blender_rendering.utils.blender import clear_orphaned_materials, remove_material_nodes, add_default_material
from amira_blender_rendering.utils import material as mutil
# from amira_blender_rendering.utils.logging import get_logger


# TODO: change into MaterialNodesMetalToolCap class
# TODO: it is really tedious and error-prone to set up materials this way. We
#       should invest the time to write a blender plugin that generates
#       python-code for us, or loads node setups from a configuration file, or
#       something along the lines...

def setup_material(material: bpy.types.Material, empty: bpy.types.Object = None):
    """Setup material nodes for the metal tool cap"""
    # TODO: refactor into smaller node-creation functions that can be re-used elsewhere

    # logger = get_logger()
    tree = material.node_tree
    nodes = tree.nodes

    # check if we have default nodes
    n_output, n_bsdf = mutil.check_default_material(material)

    # set BSDF default values
    n_bsdf.inputs['Subsurface'].default_value = 0.6
    n_bsdf.inputs['Subsurface Color'].default_value = (0.8, 0.444, 0.444, 1.0)
    n_bsdf.inputs['Metallic'].default_value = 1.0

    # thin metallic surface lines (used primarily for normal/bump map computation)
    n_texcoord_bump = nodes.new('ShaderNodeTexCoord')
    # setup empty (reference for distance computations)
    if empty is None:
        # get currently selected object
        obj = bpy.context.object

        # add empty
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.object

        # locate at the top of the object
        v0 = Vector(obj.bound_box[1])
        v1 = Vector(obj.bound_box[2])
        v2 = Vector(obj.bound_box[5])
        v3 = Vector(obj.bound_box[6])
        empty.location = (v0 + v1 + v2 + v3) / 4
        # rotate into object space. afterwards we'll have linkage via parenting
        empty.location = obj.matrix_world @ empty.location
        # copy rotation
        empty.rotation_euler = obj.rotation_euler

        # deselect all
        bpy.ops.object.select_all(action='DESELECT')

        # take care to re-select everything
        empty.select_set(state=True)
        obj.select_set(state=True)

        # make obj active again (will become parent of all selected objects)
        bpy.context.view_layer.objects.active = obj

        # make parent, keep transform
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)
    # set the empty as input for the texture
    n_texcoord_bump.object = empty

    # (dot)^2 (distance from empty)
    n_dot = nodes.new('ShaderNodeVectorMath')
    n_dot.operation = 'DOT_PRODUCT'
    tree.links.new(n_texcoord_bump.outputs['Object'], n_dot.inputs[0])
    tree.links.new(n_texcoord_bump.outputs['Object'], n_dot.inputs[1])

    n_pow = nodes.new('ShaderNodeMath')
    n_pow.operation = 'POWER'
    tree.links.new(n_dot.outputs[1], n_pow.inputs[0])

    # mapping input from empty to noise
    n_mapping = nodes.new('ShaderNodeMapping')
    tree.links.new(n_texcoord_bump.outputs['Object'], n_mapping.inputs[0])

    # generate and link up required noise textures
    n_noise0 = nodes.new('ShaderNodeTexNoise')
    n_noise0.inputs['Scale'].default_value = 1.0
    n_noise0.inputs['Detail'].default_value = 1.0
    n_noise0.inputs['Distortion'].default_value = 2.0
    tree.links.new(n_pow.outputs[0], n_noise0.inputs[0])

    n_noise1 = nodes.new('ShaderNodeTexNoise')
    n_noise1.inputs['Scale'].default_value = 300.0
    n_noise1.inputs['Detail'].default_value = 0.0
    n_noise1.inputs['Distortion'].default_value = 0.0
    tree.links.new(n_pow.outputs[0], n_noise1.inputs[0])

    # XXX: is this noise required?
    n_noise2 = nodes.new('ShaderNodeTexNoise')
    n_noise2.inputs['Scale'].default_value = 0.0
    n_noise2.inputs['Detail'].default_value = 0.0
    n_noise2.inputs['Distortion'].default_value = 0.1
    tree.links.new(n_mapping.outputs['Vector'], n_noise2.inputs[0])

    n_noise3 = nodes.new('ShaderNodeTexNoise')
    n_noise3.inputs['Scale'].default_value = 5.0
    n_noise3.inputs['Detail'].default_value = 2.0
    n_noise3.inputs['Distortion'].default_value = 0.0
    tree.links.new(n_mapping.outputs['Vector'], n_noise3.inputs[0])

    # color output
    n_colorramp_col = nodes.new('ShaderNodeValToRGB')
    n_colorramp_col.color_ramp.color_mode = 'RGB'
    n_colorramp_col.color_ramp.interpolation = 'LINEAR'
    n_colorramp_col.color_ramp.elements[0].position = 0.118
    n_colorramp_col.color_ramp.elements[1].position = 0.727
    tree.links.new(n_noise0.outputs['Fac'], n_colorramp_col.inputs['Fac'])

    n_output_color = nodes.new('ShaderNodeMixRGB')
    n_output_color.inputs['Fac'].default_value = 0.400
    n_output_color.inputs['Color1'].default_value = (0.485, 0.485, 0.485, 1.0)
    tree.links.new(n_colorramp_col.outputs['Color'], n_output_color.inputs['Color2'])

    # roughness finish
    n_mul_r = nodes.new('ShaderNodeMath')
    n_mul_r.operation = 'MULTIPLY'
    n_mul_r.inputs[1].default_value = 0.100
    tree.links.new(n_noise3.outputs['Fac'], n_mul_r.inputs[0])

    n_output_roughness = nodes.new('ShaderNodeMath')
    n_output_roughness.operation = 'ADD'
    n_output_roughness.inputs[1].default_value = 0.050
    tree.links.new(n_mul_r.outputs[0], n_output_roughness.inputs[0])

    # math nodes to mix noise with distance and get ring-effect (modulo), leading to bump map
    n_add0 = nodes.new('ShaderNodeMath')
    n_add0.operation = 'ADD'
    tree.links.new(n_pow.outputs[0], n_add0.inputs[0])
    tree.links.new(n_noise2.outputs['Fac'], n_add0.inputs[1])

    n_mul0 = nodes.new('ShaderNodeMath')
    n_mul0.operation = 'MULTIPLY'
    n_mul0.inputs[1].default_value = 300.000
    tree.links.new(n_add0.outputs[0], n_mul0.inputs[0])

    n_mod0 = nodes.new('ShaderNodeMath')
    n_mod0.operation = 'MODULO'
    n_mod0.inputs[1].default_value = 2.000
    tree.links.new(n_mul0.outputs[0], n_mod0.inputs[0])

    n_mul1 = nodes.new('ShaderNodeMath')
    n_mul1.operation = 'MULTIPLY'
    tree.links.new(n_noise1.outputs['Fac'], n_mul1.inputs[0])
    tree.links.new(n_mod0.outputs[0], n_mul1.inputs[1])

    n_min_n = nodes.new('ShaderNodeMath')
    n_min_n.operation = 'MINIMUM'
    tree.links.new(n_noise1.outputs['Fac'], n_min_n.inputs[0])
    tree.links.new(n_mul1.outputs[0], n_min_n.inputs[1])

    n_colorramp_rough = nodes.new('ShaderNodeValToRGB')
    n_colorramp_rough.color_ramp.color_mode = 'RGB'
    n_colorramp_rough.color_ramp.interpolation = 'LINEAR'
    n_colorramp_rough.color_ramp.elements[0].position = 0.159
    n_colorramp_rough.color_ramp.elements[1].position = 0.541
    tree.links.new(n_min_n.outputs[0], n_colorramp_rough.inputs[0])

    n_output_normal = nodes.new('ShaderNodeBump')
    n_output_normal.inputs['Strength'].default_value = 0.075
    n_output_normal.inputs['Distance'].default_value = 1.000
    tree.links.new(n_colorramp_rough.outputs['Color'], n_output_normal.inputs['Height'])

    # output nodes:
    #   n_output_color -> color / outputs['Color']
    #   n_output_roughness -> roughness / outputs['Value']
    #   n_output_normal -> normal / outputs['Normal']
    # hook to bsdf shader node
    tree.links.new(n_output_color.outputs['Color'], n_bsdf.inputs['Base Color'])
    tree.links.new(n_output_roughness.outputs['Value'], n_bsdf.inputs['Roughness'])
    tree.links.new(n_output_normal.outputs['Normal'], n_bsdf.inputs['Normal'])


# TODO: this should become a unit test
def main():
    """First tear down any material assigned with the object, then create everything from scratch"""
    remove_material_nodes()
    clear_orphaned_materials()
    mat = add_default_material()
    setup_material(mat)


if __name__ == "__main__":
    main()
