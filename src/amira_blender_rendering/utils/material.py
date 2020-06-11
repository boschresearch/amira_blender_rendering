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

from abc import ABC, abstractmethod
import random

import numpy as np
import bpy

from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.utils.blender import get_collection_item_names, find_new_items

logger = get_logger()


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
    for lnk in tree.links:
        if (lnk.from_node == n_bsdf) and (lnk.to_node == n_output):
            link_exists = True
            break
    if not link_exists:
        tree.links.new(n_bsdf.outputs['BSDF'], n_output.inputs['Surface'])

    return n_output, n_bsdf


def set_viewport_shader(shader="MATERIAL"):
    """Set the viewport shader, for user convenience when using GUI

    Args:
        shader (str, optional): type of shader to use from WIREFRAME, SOLID, MATERIAL, RENDERED.
        Defaults to "MATERIAL".
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = shader


class BaseMaterialGenerator(ABC):
    """Interface for material generators"""
    @abstractmethod
    def get_material(self):
        return NotImplemented


class MetallicMaterialGenerator(BaseMaterialGenerator):
    """Generate randomized metallic materials"""
    def __init__(self):
        self._rgb_lower_limits = (0.9, 0.7, 0.6)
        self._shift_to_white = 2.0
        self._max_roughness = 0.4
        self._max_texture_scale = 0.7
        self._max_texture_detail = 3.0
        self._max_texture_distortion = 0.5
        self._materials = list()

    def _clear_node_tree(self, material):
        nodes = material.node_tree.nodes
        for node in nodes:
            nodes.remove(node)

    def make_random_material(self, n=1):
        """Make a new randomized metallic material

        Args:
            n (int, optional): how many new materials to make. Defaults to 1.
        """
        for i in range(n):
            desired_name = "random_metal_{}".format(len(self._materials) + 1)
            material_name = self._make_random_material(desired_name)
            self._materials.append(material_name)

    def _make_random_material(self, desired_name):
        """Generate a randomized node-tree for a metallic material

        Args:
            desired_name (string) : the desired name for the new material

        Returns
            actual_name (string) : the actual exact material name
            Might differ from desired-name, due to blenders automatic conflict resolution (appending ".001" etc.)
        """
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

        old_names = get_collection_item_names(bpy.data.materials)
        mat = bpy.data.materials.new(desired_name)
        new_names = find_new_items(bpy.data.materials, old_names)
        if len(new_names) > 1:
            raise AssertionError("multiple new material names, cannot identify new material")
        actual_name = new_names.pop()

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

    def get_material(self):
        """Return handle to randomized metallic material

        Returns:
            bpy.types.Material: object handle to a randomized metallic material
        """
        material_name = random.sample(self._materials, 1)[0]
        return bpy.data.materials[material_name]
