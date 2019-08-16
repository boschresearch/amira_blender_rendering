#!/usr/bin/env python

import bpy
import logging
from mathutils import Vector
from amira_blender_rendering import utils
from amira_blender_rendering.blender_utils import clear_orphaned_materials, remove_material_nodes, add_default_material
from . import material_utils

# TODO: comments from material_metal_tool_cap.py apply

def setup_material(material: bpy.types.Material):

    logger = utils.get_logger()
    tree = material.node_tree
    nodes = tree.nodes

    # check if we have default nodes
    n_output, n_bsdf = material_utils.check_default_material(material)

    # setup BSDF
    n_bsdf.inputs['Base Color'].default_value = (0.668, 0.016, 0.012, 1.000)
    n_bsdf.inputs['Subsurface'].default_value = 0.010
    n_bsdf.inputs['Subsurface Color'].default_value = (0.395, 0.038, 0.040, 1.000)
    n_bsdf.inputs['Metallic'].default_value = 0.0

    # procedural roughness  setup
    n_noise_rough = nodes.new('ShaderNodeTexNoise')
    n_noise_rough.inputs['Scale'].default_value      = 5.0
    n_noise_rough.inputs['Detail'].default_value     = 2.0
    n_noise_rough.inputs['Distortion'].default_value = 0.0

    n_ramp_rough = nodes.new('ShaderNodeValToRGB')
    n_ramp_rough.color_ramp.color_mode = 'RGB'
    n_ramp_rough.color_ramp.interpolation = 'LINEAR'
    n_ramp_rough.color_ramp.elements[0].position = 0.382
    n_ramp_rough.color_ramp.elements[1].position = 1.000

    n_value = nodes.new('ShaderNodeValue')
    n_value.outputs['Value'].default_value = 0.800

    n_overlay = nodes.new('ShaderNodeMixRGB')
    n_overlay.blend_type = 'OVERLAY'
    n_overlay.use_clamp = True
    n_overlay.inputs['Fac'].default_value = 0.625

    tree.links.new(n_noise_rough.outputs['Fac'], n_ramp_rough.inputs['Fac'])
    tree.links.new(n_value.outputs['Value'], n_overlay.inputs['Color1'])
    tree.links.new(n_ramp_rough.outputs['Color'], n_overlay.inputs['Color2'])
    tree.links.new(n_overlay.outputs['Color'], n_bsdf.inputs['Roughness'])

    # normal / bump map
    n_noise_bump = nodes.new('ShaderNodeTexNoise')
    n_noise_bump.inputs['Scale'].default_value      = 800.0
    n_noise_bump.inputs['Detail'].default_value     =  16.0
    n_noise_bump.inputs['Distortion'].default_value =   0.0
    n_bump = nodes.new('ShaderNodeBump')
    n_bump.inputs['Strength'].default_value = 0.010
    n_bump.inputs['Distance'].default_value = 0.100
    tree.links.new(n_noise_bump.outputs['Fac'], n_bump.inputs['Height'])
    tree.links.new(n_bump.outputs['Normal'], n_bsdf.inputs['Normal'])


    # displacement map
    n_texcoord       = nodes.new('ShaderNodeTexCoord')
    n_mapping        = nodes.new('ShaderNodeMapping')
    n_sepxyz         = nodes.new('ShaderNodeSeparateXYZ')
    n_combxyz_ease   = nodes.new('ShaderNodeCombineXYZ')
    n_combxyz_spline = nodes.new('ShaderNodeCombineXYZ')

    n_noise_disp = nodes.new('ShaderNodeTexNoise')
    n_noise_disp.inputs['Scale'].default_value      = 15.2
    n_noise_disp.inputs['Detail'].default_value     =  5.0
    n_noise_disp.inputs['Distortion'].default_value =  0.0

    n_wave = nodes.new('ShaderNodeTexWave')
    n_wave.wave_type = 'BANDS'
    n_wave.wave_profile = 'SIN'
    n_wave.inputs['Scale'].default_value        = 50.0
    n_wave.inputs['Distortion'].default_value   =  5.0
    n_wave.inputs['Detail'].default_value       =  1.0
    n_wave.inputs['Detail Scale'].default_value =  1.0

    n_ramp_ease = nodes.new('ShaderNodeValToRGB')
    n_ramp_ease.color_ramp.color_mode = 'RGB'
    n_ramp_ease.color_ramp.interpolation = 'EASE'
    n_ramp_ease.color_ramp.elements[0].position = 0.236
    n_ramp_ease.color_ramp.elements[1].position = 1.000

    n_ramp_spline = nodes.new('ShaderNodeValToRGB')
    n_ramp_spline.color_ramp.color_mode = 'RGB'
    n_ramp_spline.color_ramp.interpolation = 'B_SPLINE'
    n_ramp_spline.color_ramp.elements[0].position = 0.214
    n_ramp_spline.color_ramp.elements[1].position = 1.000

    n_mix = nodes.new('ShaderNodeMixRGB')
    n_mix.blend_type = 'MIX'
    n_mix.use_clamp = False
    n_mix.inputs['Color2'].default_value = (.5, .5, .5, 1.0)

    tree.links.new(n_texcoord.outputs['Object'], n_mapping.inputs['Vector'])
    tree.links.new(n_mapping.outputs['Vector'], n_sepxyz.inputs['Vector'])
    tree.links.new(n_sepxyz.outputs['Z'], n_combxyz_ease.inputs['Z'])
    tree.links.new(n_sepxyz.outputs['Z'], n_combxyz_spline.inputs['Z'])
    tree.links.new(n_combxyz_ease.outputs['Vector'], n_noise_disp.inputs['Vector'])
    tree.links.new(n_combxyz_spline.outputs['Vector'], n_wave.inputs['Vector'])
    tree.links.new(n_noise_disp.outputs['Color'], n_ramp_ease.inputs['Fac'])
    tree.links.new(n_wave.outputs['Color'], n_ramp_spline.inputs['Fac'])
    tree.links.new(n_ramp_ease.outputs['Color'], n_mix.inputs['Fac'])
    tree.links.new(n_ramp_spline.outputs['Color'], n_mix.inputs['Color1'])
    tree.links.new(n_mix.outputs['Color'], n_output.inputs['Displacement'])

