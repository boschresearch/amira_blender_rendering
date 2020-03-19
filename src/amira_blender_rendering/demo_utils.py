#!/usr/bin/env python

import bpy
from amira_blender_rendering.utils import load_img

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


def get_mesh_bounding_box(mesh):
    """Returns Bounding-Box of Mesh-Object at zero position (Edit mode)"""

    try:
        xyz = mesh.data.vertices[0].co
    except AttributeError as err:
        print('expecting a mesh object, but no data.vertices attribute in object {}'.format(mesh))
        raise err

    bb = [[xyz[0], xyz[0]], [xyz[1], xyz[1]], [xyz[2], xyz[2]]]
    for v in mesh.data.vertices:
        xyz = v.co
        for i in range(3):
            bb[i][0] = min(bb[i][0], xyz[i])
            bb[i][1] = max(bb[i][1], xyz[i])

    bounding_box = BoundingBox3D(bb[0][0], bb[0][1], bb[1][0], bb[1][1], bb[2][0], bb[2][1])
    return bounding_box


class Range1D():

    def __init__(self, _min, _max):
        if _max < _min:
            raise AssertionError('_max {} must be greater than _min {}'.format(_max, _min))
        self.min = _min
        self.max = _max


class BoundingBox3D():

    def __init__(self, x_min, x_max, y_min, y_max, z_min, z_max):
        self.x = Range1D(x_min, x_max)
        self.y = Range1D(y_min, y_max)
        self.z = Range1D(z_min, z_max)



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



