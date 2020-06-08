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

import bpy
import logging
from amira_blender_rendering import utils
from amira_blender_rendering.utils.logging import get_logger


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
