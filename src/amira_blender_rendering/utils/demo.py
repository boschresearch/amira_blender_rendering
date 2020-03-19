#!/usr/bin/env python

import bpy
from amira_blender_rendering import utils
from amira_blender_rendering.utils import load_img

assets_dir = utils.expandpath("$AMIRA_BLENDER_RENDERING_ASSETS")

def create_room_corner():
    bpy.ops.mesh.primitive_plane_add(
        # radius=1,  # 2.79 uses radius[=1], 2.8 uses size[=2]
        location=(0.0, 0.0, 0.0),)
    floor = bpy.context.active_object
    floor.name = "Floor"
    set_image_texture(
        floor,
        osp.join(assets_dir, "concrete_cracked_03-color.png"),
        "concrete_cracked_03",
    )

    bpy.ops.mesh.primitive_plane_add(
        location=(0.0, -1.0, 1.0),
        rotation=(0.5 * np.pi, 0.0, 0.0),
    )
    wall_1 = bpy.context.active_object
    wall_1.name = "Wall_1"
    set_image_texture(
        wall_1,
        osp.join(assets_dir, "brick_simple_45-color.jpg"),
        "brick_simple_45",
    )

    bpy.ops.mesh.primitive_plane_add(
        location=(-1.0, 0.0, 1.0),
        rotation=(0.5 * np.pi, 0.0, 0.5 * np.pi),
    )
    wall_2 = bpy.context.active_object
    wall_2.name = "Wall_2"
    set_image_texture(
        wall_2,
        osp.join(assets_dir, "brick_simple_45-color.jpg"),
        "brick_simple_45",
    )


def load_cad_part(cad_part):
    current_objects = bpy.data.objects.keys()
    blendfile = osp.join(assets_dir, "CAD_parts_{}.blend")
    blendfile = blendfile.format(280)
    bpy.ops.wm.append(filename=cad_part, directory=blendfile + "\\Object\\")
    for o in bpy.data.objects.keys():
        if o not in current_objects:
            return bpy.data.objects[o]


def set_image_texture(obj, image_path, material_name):

    COL_WIDTH = 200

    img = load_img(image_path)

    clc = obj.data.uv_layers
    if len(clc) == 0:
        clc.new()

    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    obj.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    # TODO : might be unnecessary, check prepending ShaderNodeTexImage to default nodes
    for node in nodes:
        nodes.remove(node)

    links = mat.node_tree.links

    nodes.new(type='ShaderNodeTexImage')
    nodes[-1].name = "Image"
    nodes["Image"].location = (0, 0)
    nodes["Image"].image = img

    nodes.new(type='ShaderNodeBsdfDiffuse')
    nodes[-1].name = "Diffuse"
    nodes["Diffuse"].location = (COL_WIDTH, 0)

    links.new(nodes["Diffuse"].inputs["Color"], nodes["Image"].outputs["Color"])

    nodes.new(type='ShaderNodeOutputMaterial')
    nodes[-1].name = "Out"
    nodes["Out"].location = (2 * COL_WIDTH, 0)

    links.new(nodes["Out"].inputs["Surface"], nodes["Diffuse"].outputs[0])


def translate_object(obj, translation: tuple):
    obj.location += Vector(translation)



