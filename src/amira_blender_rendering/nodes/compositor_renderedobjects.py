#!/usr/bin/env python

from typing import List
import bpy


def setup_compositor_nodes_rendered_objects(
        base_path: str,
        objs : List[bpy.types.Object],
        scene: bpy.types.Scene = bpy.context.scene):

    """Setup all compositor nodes that are required for exporting to the
    RenderObjects dataset format."""

    # enable nodes, and enable object index pass (required for mask)
    scene.use_nodes = True
    scene.view_layers['View Layer'].use_pass_object_index = True
    tree = scene.node_tree
    nodes = tree.nodes
    n_render_layers = nodes['Render Layers']

    # add file output node and setup format (16bit RGB without alpha channel)
    n_output_file = nodes.new('CompositorNodeOutputFile')
    n_output_file.base_path = base_path
    n_output_file.format.color_mode = 'RGB'
    n_output_file.format.color_depth = '16'

    # setup sockets/slots. First is RGBA Image by default
    s_render = n_output_file.file_slots[0]
    s_render.use_node_format = True
    s_render.path = 'Render.'
    tree.links.new(n_render_layers.outputs['Image'], n_output_file.inputs['Image'])

    # add all aditional file slots, e.g. depth map, image masks, backdrops, etc.
    n_output_file.file_slots.new('Depth')
    s_depth_map = n_output_file.file_slots['Depth']
    s_depth_map.use_node_format = False
    s_depth_map.format.file_format = 'OPEN_EXR'
    s_depth_map.format.use_zbuffer = True
    s_depth_map.path = 'Depth.'
    tree.links.new(n_render_layers.outputs['Depth'], n_output_file.inputs['Depth'])

    # backdrop setup (mask without any object)
    n_id_mask = nodes.new('CompositorNodeIDMask')
    n_id_mask.index = 0
    n_id_mask.use_antialiasing = True
    tree.links.new(n_render_layers.outputs['IndexOB'], n_id_mask.inputs['ID value'])

    mask_name = f"Backdrop"
    n_output_file.file_slots.new(mask_name)
    s_obj_mask = n_output_file.file_slots[mask_name]
    s_obj_mask.use_node_format = True
    s_obj_mask.path = f"{mask_name}."
    tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])

    # add nodes and sockets for all masks
    for i, obj in enumerate(objs):
        # setup object (this will change the pass index). The pass_index must be > 0 for the mask to work.
        obj.pass_index = i+1

        # mask
        n_id_mask = nodes.new('CompositorNodeIDMask')
        n_id_mask.index = obj.pass_index
        n_id_mask.use_antialiasing = True
        tree.links.new(n_render_layers.outputs['IndexOB'], n_id_mask.inputs['ID value'])

        # socket in file output
        mask_name = f"Mask{i:03}"
        n_output_file.file_slots.new(mask_name)
        s_obj_mask = n_output_file.file_slots[mask_name]
        s_obj_mask.use_node_format = True
        s_obj_mask.path = f"{mask_name}."
        tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])

