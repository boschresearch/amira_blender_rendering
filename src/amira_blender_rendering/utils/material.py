#!/usr/bin/env python

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
