"""Generate Composite-Node Materials

Generates RGD, Depth, Part-ID masks
"""
# TODO:
# 1. change to MaterialNodeDriver class (hide: nodes, root_node, links), 
# and use specialized material classes
# 2. Depth should act at scene level (as-is), 
# but it will probably be simpler to apply Part-ID at Object level;
# especially for instance masks and Part-IDs for multiple instance-types
# 3. Randomization, e.g. of hue, and roughness for Metal parts (use "Metal" in material names?)
# 4. Using bumps, espeacially on metalic\glossy parts 

import os.path as osp

import bpy

from amira_blender_rendering import utils

logger = utils.get_logger()

# node layout parameters, no affect on functionality
col_width, row_height = 200, -180


def set_materials(out_parent,
                  scene=None,
                  render_layer=None,
                  depth=True,
                  part_id=True,
                  remove_current_nodes=True,
                  max_depth=5):
    """Adds Depths, and ID-Masks

    RGB is left untouched
    """
    logger.debug("starting set_materials")
    # out_parent = "/home/yoelsh/work/amira_tools/amira_blender_rendering/out"

    if scene is None:
        scene = bpy.data.scenes[0]
    scene.use_nodes = True
    scene.render.use_compositing = True

    if render_layer is None:
        render_layer = 0
    render_layer_obj = bpy.context.scene.render.layers[render_layer]
    render_layer_obj.use_pass_object_index = True

    nodes = scene.node_tree.nodes
    if remove_current_nodes:
        logger.debug("removing pre-exisiting nodes")
        remove_nodes(scene)

    links = scene.node_tree.links

    nodes.new(type="CompositorNodeRLayers")
    nodes[-1].name = "Root"
    nodes["Root"].location = (0, 0)

    set_rgb(osp.join(out_parent, "RGB"), nodes, "Root", links)

    if depth:
        set_depth(osp.join(out_parent, "Depth"), nodes, "Root", links, max_depth=max_depth)

    if part_id:
        set_part_id(osp.join(out_parent, "Part_ID"), nodes, "Root", links)


def remove_nodes(scene):
    nodes = scene.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


def disable_nodes(scene):
    scene.use_nodes = False
    scene.render.use_compositing = False
    remove_nodes(scene)


def set_rgb(rgb_out, nodes, root_node, links):

    nodes.new(type="CompositorNodeOutputFile")
    nodes[-1].name = "RGB_Out"
    nodes["RGB_Out"].location = (col_width, 0)
    nodes["RGB_Out"].format.file_format = "JPEG"
    nodes["RGB_Out"].base_path = rgb_out
    links.new(nodes["RGB_Out"].inputs[0], nodes[root_node].outputs["Image"])

    logger.info("directing RGB to {}".format(rgb_out))


def set_depth(depth_out, nodes, root_node, links, max_depth=5):

    nodes.new(type="CompositorNodeMath")
    nodes[-1].name = "Depth_Div"
    nodes["Depth_Div"].location = (col_width, row_height)
    nodes["Depth_Div"].operation = "DIVIDE"
    nodes["Depth_Div"].inputs[1].default_value = max_depth
    links.new(nodes["Depth_Div"].inputs[0], nodes[root_node].outputs["Depth"])

    nodes.new(type="CompositorNodeOutputFile")
    nodes[-1].name = "Depth_Out"
    nodes["Depth_Out"].location = (2 * col_width, row_height)
    nodes["Depth_Out"].format.file_format = "JPEG"
    nodes["Depth_Out"].base_path = depth_out
    links.new(nodes["Depth_Out"].inputs[0], nodes["Depth_Div"].outputs[0])

    logger.info("directing Depth to {}".format(depth_out))


def set_part_id(id_out, nodes, root_node, links, max_id=255):
    """ID label is determined by object pass-index"""
    nodes.new(type="CompositorNodeMath")
    nodes[-1].name = "ID_Div"
    nodes["ID_Div"].location = (col_width, 2 * row_height)
    nodes["ID_Div"].operation = "DIVIDE"
    nodes["ID_Div"].inputs[1].default_value = max_id
    links.new(nodes["ID_Div"].inputs[0], nodes[root_node].outputs["IndexOB"])

    nodes.new(type="CompositorNodeOutputFile")
    nodes[-1].name = "ID_Out"
    nodes["ID_Out"].location = (2 * col_width, 2 * row_height)
    nodes["ID_Out"].format.file_format = "BMP"
    nodes["ID_Out"].base_path = id_out
    links.new(nodes["ID_Out"].inputs[0], nodes["ID_Div"].outputs[0])

    logger.info("directing Part-IDs to {}".format(id_out))
