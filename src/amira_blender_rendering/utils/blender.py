#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bpy
from mathutils import Vector

from amira_blender_rendering.utils.logging import get_logger


def get_collection_item_names(bpy_collection):
    """Get names of current items in a blender collection, e.g. object names in bpy.data.objects

    Args:
        bpy_collection : a blender iterable, where items are a tuple, and the 1st item element is a name string

    Returns:
        list of strings : names of items currenlty in collection
    """
    names = list()
    for item in bpy_collection.items():
        names.append(item[0])
    return names


def find_new_items(bpy_collection, old_names):
    """Ascertian new item names, given a list of old item names

    Args:
        bpy_collection : a blender iterable, where items are a tuple, and the 1st item element is a name string

    Returns:
        set of strings : names of items currenlty in collection

    Usage:
        Intended usage is to verify the assigned name to a new item (object, material, etc.)
        This is needed due to blender's automatic name conflict resolution, i.e. apending ".001" etc.
    """
    new_names = get_collection_item_names(bpy_collection)
    return set(new_names).difference(old_names)


def unlink_objects():
    for scene in bpy.data.scenes:
        for c in scene.collection.children:
            scene.collection.children.unlink(c)


def remove_nodes(scene):
    nodes = scene.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


def disable_nodes(scene):
    scene.use_nodes = False
    scene.render.use_compositing = False
    remove_nodes(scene)


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
        get_logger().warn("No CUDA compute device available, will use CPU")
    else:
        # device_set = False  # FIXME: unused variable
        for d in prefs.devices:
            if d.type == 'CUDA':
                get_logger().info(f"Using CUDA device '{d.name}' ({d.id})")
                d.use = True
            else:
                d.use = False

        # using the current scene, enable GPU Compute for rendering
        bpy.context.scene.cycles.device = 'GPU'


def clear_all_objects():
    """Remove all objects, meshes, lights, and cameras from a scene"""

    unlink_objects()
    data_collections = list((
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.cameras,
    ))
    data_collections.append(bpy.data.lights)

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


def select_object(obj_name: str):
    """Select and activate an object given its name"""
    if obj_name not in bpy.data.objects:
        get_logger().warn(f"Could not find object {obj_name}")
        return

    # we first deselect all, then select and activate the target object
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects[obj_name]
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def add_default_material(obj: bpy.types.Object = bpy.context.object,
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


def import_object(blendfile: str, obj: str):
    """Import an object from a blender Library file to the currently loaded file.

    Note: this function is a synonym for append_object.
    """
    append_object(blendfile, obj)


def append_object(blendfile: str, obj: str):
    """Append an object from a blender Lirbary file to the currently loaded file.

    Args:
        blendfile (str): path on disk to blender file
        obj (str): Name of object in blender file
    """
    # blender files are organized in directories or sections
    section_object = '/Object/'
    # the path specifies where the object is inside the blender file
    path = blendfile + section_object + obj
    # the directory where to look for the object
    dir = blendfile + section_object
    # this call blenders Wm operator to append from blender file. For more
    # documentation, see https://docs.blender.org/api/current/bpy.ops.wm.html
    bpy.ops.wm.append(filepath=path, filename=obj, directory=dir)


def remove_material_nodes(obj: bpy.types.Object = bpy.context.object):
    """Remove all material nodes from an object"""
    obj.data.materials.clear()


def look_at(obj: bpy.types.Object, target: Vector):
    """Rotate an object such that it looks at a target.

    The object's Y axis will point upwards, and the -Z axis towards the
    target. This is the 'correct' rotation for cameras and lights."""
    t = obj.location
    dir = target - t
    quat = dir.to_track_quat('-Z', 'Y')
    obj.rotation_euler = quat.to_euler()


def delete_object(object_name):
    """Delete an object given its name.

    This will also remove the meshes associated with the object.

    Args:
        object_name (str, bpy.types.Object): Either pass the object's name, or
            the object
    """

    # try to get the object name
    logger = get_logger()
    if not isinstance(object_name, str):
        try:
            object_name = object_name.name
        except AttributeError as err:
            logger.error("Expecting name string but got: {}".format(object_name))
            raise err
    if object_name not in bpy.data.objects:
        logger.warning(f"Could not find object {object_name}")
        return

    select_object(object_name)
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
    already available.

    Args:
        filepath (str): image file path

    Returns:
        bpy.types.Image"""
    for img in bpy.data.images:
        if img.filepath == filepath:
            return img
    return bpy.data.images.load(filepath)


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


def get_mesh_bounding_box(mesh):
    """Returns Bounding-Box of Mesh-Object at zero position (Edit mode)"""

    try:
        xyz = mesh.data.vertices[0].co
    except AttributeError as err:
        get_logger().error('expecting a mesh object, but no data.vertices attribute in object {}'.format(mesh))
        raise err

    bb = [[xyz[0], xyz[0]], [xyz[1], xyz[1]], [xyz[2], xyz[2]]]
    for v in mesh.data.vertices:
        xyz = v.co
        for i in range(3):
            bb[i][0] = min(bb[i][0], xyz[i])
            bb[i][1] = max(bb[i][1], xyz[i])

    bounding_box = BoundingBox3D(bb[0][0], bb[0][1], bb[1][0], bb[1][1], bb[2][0], bb[2][1])
    return bounding_box
