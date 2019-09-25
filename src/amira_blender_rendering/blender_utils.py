#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path as osp
import numpy as np

import bpy
from mathutils import Vector

from amira_blender_rendering import utils

pkg_dir = utils.get_my_dir(__file__)
assets_dir = osp.join(pkg_dir, "assets")

logger = utils.get_logger()

version_ge_2_8 = bpy.app.version[1] >= 80


def _unlink_279():
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            try:
                scene.objects.unlink(obj)
            except RuntimeError:
                bpy.data.objects[obj.name].select = True
                bpy.context.scene.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT')
                scene.objects.unlink(obj)


def _unlink_280():
    for scene in bpy.data.scenes:
        for c in scene.collection.children:
            scene.collection.children.unlink(c)


def activate_cuda_devices():
    """This function tries to activate all CUDA devices for rendering"""

    # get cycles preferences
    cycles = bpy.context.preferences.addons['cycles']
    prefs = cycles.preferences

    # set CUDA enabled, and activate all GPUs we have access to
    prefs.compute_device_type = 'CUDA'

    # determine if we have a GPU available
    cuda_available = False
    for d in prefs.get_devices()[0]:
        cuda_available = cuda_available or d.type == 'CUDA'

    # if we don't have a GPU available, then print a warning
    if not cuda_available:
        print("WW: No CUDA compute device available, will use CPU")
    else:
        device_set = False
        for d in prefs.devices:
            if d.type == 'CUDA':
                print(f"II: Using CUDA device '{d.name}' ({d.id})")
                d.use = True
            else:
                d.use = False

        # using the current scene, enable GPU Compute for rendering
        bpy.context.scene.cycles.device = 'GPU'


def clear_all_objects():
    """Remove all objects, meshes, lights, and cameras from a scene"""

    if version_ge_2_8:
        _unlink_280()
    else:
        _unlink_279()

    data_collections = list((
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.cameras,
    ))
    if version_ge_2_8:
        data_collections.append(bpy.data.lights)
    else:
        data_collections.append(bpy.data.lamps)

    for clc in data_collections:
        for id_data in clc:
            clc.remove(id_data)


def clear_orphaned_materials():
    """Remove all materials without user"""
    mats = []
    for mat in bpy.data.materials:
        if mat.users == 0:
            mats.append(mat)

    for mat in mats:
        mat.user_clear()
        bpy.data.materials.remove(mat)


def add_default_material(
    obj: bpy.types.Object = bpy.context.object,
    name: str = 'DefaultMaterial') -> bpy.types.Material:

    """Add a new 'default' Material to an object.

    This material will automatically create a Principled BSDF node as well as a Material Output node."""

    # TODO: select the object if it is not bpy.context.object, and after setting
    # up the material, deselect it again

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return mat


def remove_material_nodes(obj: bpy.types.Object = bpy.context.object):
    """Remove all material nodes from an object"""
    obj.data.materials.clear()


def look_at(obj : bpy.types.Object, target : Vector):
    """Rotate an object such that it looks at a target.

    The object's Y axis will point upwards, and the -Z axis towards the
    target. This is the 'correct' rotation for cameras and lights."""
    t = obj.location
    dir = target - t
    quat = dir.to_track_quat('-Z', 'Y')
    obj.rotation_euler = quat.to_euler()



def delete_object(object_name):

    if not isinstance(object_name, str):
        try:
            object_name = object_name.name
        except AttributeError as err:
            logger.error("Expecting name string but got: {}".format(object_name))
            raise err

    bpy.ops.object.select_all(action='DESELECT')
    if object_name in bpy.data.objects:
        try:
            bpy.data.objects[object_name].select = True  # Blender 2.7x
        except Exception:
            # https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Scene_and_Object_API
            bpy.data.objects[object_name].select_set(True)  # Blender 2.8x
    else:
        logger.warning("could not find object {}".format(object_name))

    meshes_to_remove = list()
    for ob in bpy.context.selected_objects:
        meshes_to_remove.append(ob.data)

    bpy.ops.object.delete()

    for mesh in meshes_to_remove:
        try:  # might data be a non-mesh ?
            bpy.data.meshes.remove(mesh)
        except Exception as err:
            logger.error(str(err))


def load_img(filepath):
    """Load an image from filepath, or simply return the data block if
    already available"""
    for img in bpy.data.images:
        if img.filepath == filepath:
            return img
    return bpy.data.images.load(filepath)


def set_image_texture(obj, image_path, material_name):

    COL_WIDTH = 200

    img = load_img(image_path)

    if version_ge_2_8:
        clc = obj.data.uv_layers
    else:
        clc = obj.data.uv_textures
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
    if version_ge_2_8:
        blendfile = blendfile.format(280)
    else:
        blendfile = blendfile.format(279)
    bpy.ops.wm.append(filename=cad_part, directory=blendfile + "\\Object\\")
    for o in bpy.data.objects.keys():
        if o not in current_objects:
            return bpy.data.objects[o]


def translate_object(obj, translation: tuple):
    obj.location += Vector(translation)


def get_mesh_bounding_box(mesh):
    """Returns Bounding-Box of Mesh-Object at zero position (Edit mode)"""

    # XXX: what type is mesh of? if it is a bpy.types.object, then it has
    # property .bound_box
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
