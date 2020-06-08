#!/usr/bin/env python

import random

import numpy as np
import bpy

from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.utils.blender import get_current_items, find_new_items

logger = get_logger()


def set_viewport_shader(shader="MATERIAL"):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = shader


class MetallicMaterialGenerator(object):
    """Generate randomized metallic materials"""
    def __init__(self):
        self._rgb_lower_limits = (0.9, 0.7, 0.6)
        self._shift_to_white = 2.0
        self._max_roughness = 0.4
        self._max_texture_scale = 0.7
        self._max_texture_detail = 3.0
        self._max_texture_distortion = 0.5
        self._materials = list()

    def make_random_material(self, n=1):
        """Make a new randomized metallic material

        Keyword Arguments:
            n {int} -- how many new materials to make (default: {1})
        """
        for i in range(n):
            desired_name = "random_metal_{}".format(len(self._materials) + 1)
            material_name = self._make_random_material(desired_name)
            self._materials.append(material_name)

    def _make_random_material(self, desired_name):
        """Generate a randomized node-tree for a metallic material"""

        roughness, texture_scale, texture_detail, texture_distortion = np.random.rand(4)
        roughness *= self._max_roughness
        texture_scale *= self._max_texture_scale
        texture_detail *= self._max_texture_detail
        texture_distortion *= self._max_texture_distortion

        color = np.random.rand(4)
        color[3] = 1.0   # alpha, 1 = opaque
        for i in range(3):
            limit = self._rgb_lower_limits[i]
            color[i] = limit + (1.0 - limit) * (1.0 - color[i] ** self._shift_to_white)
        logger.debug("color: {}".format(color))

        old_names = get_current_items(bpy.data.materials)
        mat = bpy.data.materials.new(desired_name)
        new_names = find_new_items(bpy.data.materials, old_names)
        if len(new_names) > 1:
            raise AssertionError("multiple new material names, cannot identify new material")
        actual_name = new_names[0]

        mat.use_nodes = True
        self._clear_node_tree(mat)

        out_node = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (0, 0)

        glossy_node = mat.node_tree.nodes.new("ShaderNodeBsdfGlossy")
        glossy_node.location = (-200, 100)
        glossy_node.inputs["Color"].default_value = color
        glossy_node.inputs["Roughness"].default_value = roughness

        mat.node_tree.links.new(
            mat.node_tree.nodes["Material Output"].inputs["Surface"],
            mat.node_tree.nodes["Glossy BSDF"].outputs["BSDF"],
        )

        bump_node = mat.node_tree.nodes.new("ShaderNodeBump")
        bump_node.location = (-200, -100)

        mat.node_tree.links.new(
            mat.node_tree.nodes["Material Output"].inputs["Displacement"],
            mat.node_tree.nodes["Bump"].outputs["Normal"],
        )

        noise_node = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        noise_node.location = (-400, -100)
        noise_node.noise_dimensions = "3D"
        noise_node.inputs["Scale"].default_value = texture_scale
        noise_node.inputs["Detail"].default_value = texture_detail
        noise_node.inputs["Distortion"].default_value = texture_distortion

        mat.node_tree.links.new(
            mat.node_tree.nodes["Bump"].inputs["Normal"],
            mat.node_tree.nodes["Noise Texture"].outputs["Fac"],
        )

        return actual_name

    def get_random_material(self):
        """return handle to randomized metallic material"""
        material_name = random.sample(self._materials, 1)[0]
        return bpy.data.materials[material_name]

    def _clear_node_tree(self, material):
        nodes = material.node_tree.nodes
        for node in nodes:
            nodes.remove(node)


def check_default_material(material: bpy.types.Material):
    """This function checks if, given a material, the default nodes are present.
    If not, they will be set up.

    Args:
        material(bpy.types.Material): material to check

    Returns
        tuple containing the output node, and the bsdf node
    """

    logger = get_logger()
    tree = material.node_tree
    nodes = tree.nodes

    # check if default principles bsdf + metarial output exist
    if len(nodes) != 2:
        logger.warn("More shader nodes in material than expected!")

    # find if the material output node is available. If not, create it
    if 'Material Output' not in nodes:
        logger.warn("Node 'Material Output' not found in material node-tree")
        n_output = nodes.new('ShaderNodeOutputMaterial')
    else:
        n_output = nodes['Material Output']

    # find if the principled bsdf node is available. If not, create it
    if 'Principled BSDF' not in nodes:
        logger.warn("Node 'Principled BSDF' not found in material node-tree")
        n_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    else:
        n_bsdf = nodes['Principled BSDF']

    # check if link from BSDF to output is available
    link_exists = False
    for l in tree.links:
        if (l.from_node == n_bsdf) and (l.to_node == n_output):
            link_exists = True
            break
    if not link_exists:
        tree.links.new(n_bsdf.outputs['BSDF'], n_output.inputs['Surface'])

    return n_output, n_bsdf
