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

    _unlink_280()
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
        logger.warn(f"Could not find object {obj_name}")
        return

    # we first deselect all, then select and activate the target object
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects[obj_name]
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


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
    """Delete an object given its name.

    This will also remove the meshes associated with the object.

    Args:
        object_name (str, bpy.types.Object): Either pass the object's name, or
            the object
    """

    # try to get the object name
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

