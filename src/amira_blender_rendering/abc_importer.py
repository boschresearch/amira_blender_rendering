#!/usr/bin/env python3
import os
import os.path as osp
import shutil
import random
import numpy as np

import bpy

# import utils.logging.get_logger as get_logger
# from utils.logging import get_logger
import amira_blender_rendering.utils.logging as log_utils

logger = log_utils.get_logger()


def _get_current_items(bpy_collection):
    names = list()
    for item in bpy_collection.items():
        names.append(item[0])
    return names


def _find_new_items(bpy_collection, old_names):
    new_names = _get_current_items(bpy_collection)
    diff = list()
    for n_item in new_names:
        if n_item not in old_names:
            diff.append(n_item)
    return diff


def _set_viewport_shader(shader="MATERIAL"):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = shader


class MetallicMaterialGenerator(object):
    """Generate randomized metallic materials"""
    def __init__(self):
        self._rgb_lower_limits = (0.9, 0.7, 0.6)
        self._shift_to_white = 2.0
        self._max_roughness = 0.4
        self._max_texture_scale = 0.7
        self._max_texture_detail = 3.0
        self._max_texture_distortion = 0.5
        self._materials = list()

    def make_random_material(self, n=1):
        """Make a new randomized metallic material

        Keyword Arguments:
            n {int} -- how many new materials to make (default: {1})
        """
        for i in range(n):
            desired_name = "random_metal_{}".format(len(self._materials) + 1)
            material_name = self._make_random_material(desired_name)
            self._materials.append(material_name)

    def _make_random_material(self, desired_name):
        """Generate a randomized node-tree for a metallic material"""

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

        old_names = _get_current_items(bpy.data.materials)
        mat = bpy.data.materials.new(desired_name)
        new_names = _find_new_items(bpy.data.materials, old_names)
        if len(new_names) > 1:
            raise AssertionError("multiple new material names, cannot identify new material")
        actual_name = new_names[0]

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

    def get_random_material(self):
        """return handle to randomized metallic material"""
        material_name = random.sample(self._materials, 1)[0]
        return bpy.data.materials[material_name]

    def _clear_node_tree(self, material):
        nodes = material.node_tree.nodes
        for node in nodes:
            nodes.remove(node)


class ABCImporter(object):
    """Import ABC STL into blender session and assign a material"""
    def __init__(self, data_dir=None, n_materials=3):
        self._parent = self._get_abc_parent_dir(data_dir)
        self._material_generator = MetallicMaterialGenerator()
        self._material_generator.make_random_material(n_materials)
        self._object_types_map = self._get_object_types_map()

    @property
    def object_types(self):
        """Supported object types

        Returns:
            [list of strings] -- Supported object types
        """
        return sorted(key for key in self._object_types_map)

    def _get_object_types_map(self):
        object_types_map = dict(
            bearings=dict(folder="Bearings", lower_limit=0.01, upper_limit=0.1),
            sprocket=dict(folder="Sprockets", lower_limit=0.01, upper_limit=0.15),
            spring=dict(folder="Springs", lower_limit=0.01, upper_limit=0.2),
            flange=dict(folder="Unthreaded_Flanges", lower_limit=0.01, upper_limit=0.3),
            bracket=dict(folder="Brackets", lower_limit=0.01, upper_limit=0.3),
            collet=dict(folder="Collets", lower_limit=0.01, upper_limit=0.1),
            pipe=dict(folder="Pipes", lower_limit=0.01, upper_limit=0.4),
            pipe_fitting=dict(folder="Pipe_Fittings", lower_limit=0.01, upper_limit=0.15),
            pipe_joint=dict(folder="Pipe_Joints", lower_limit=0.01, upper_limit=0.2),
            bushing=dict(folder="Bushing", lower_limit=0.01, upper_limit=0.15),
            roller=dict(folder="Rollers", lower_limit=0.01, upper_limit=0.1),
            busing_liner=dict(folder="Bushing_Damping_Liners", lower_limit=0.01, upper_limit=0.15),
            shaft=dict(folder="Shafts", lower_limit=0.01, upper_limit=0.3),
            bolt=dict(folder="Bolts", lower_limit=0.01, upper_limit=0.1),
            headless_screw=dict(folder="HeadlessScrews", lower_limit=0.01, upper_limit=0.05),
            flat_screw=dict(folder="Slotted_Flat_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            hex_screw=dict(folder="Hex_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            socket_screw=dict(folder="Socket_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            nut=dict(folder="Nuts", lower_limit=0.01, upper_limit=0.05),
            push_ring=dict(folder="Push_Rings", lower_limit=0.01, upper_limit=0.05),
            retaining_ring=dict(folder="Retaining_Rings", lower_limit=0.01, upper_limit=0.05),
            washer=dict(folder="Washers", lower_limit=0.01, upper_limit=0.05),
        )

        missing = 0
        verified_types = dict()
        for obj in object_types_map:
            subfolder = object_types_map[obj]["folder"]
            if osp.isdir(osp.join(self._parent, subfolder)):
                verified_types[obj] = object_types_map[obj]
            else:
                missing += 1
                logger.warning("did not find a sub-directory corrseponding to: {}".format(obj))
        if missing > 0:
            logger.warning("MISSING {} object-type subdirs in parent directory {}".format(missing, self._parent))

        return verified_types

    @staticmethod
    def _get_abc_parent_dir(data_dir):
        if data_dir is None:
            # expecting a shared workspace for repos: amira_blender_rendering, amira_data_gfx
            # path = .../workspace/amira_blender_rendering/src/amira_blender_rendering/abc_importer.py
            parts = __file__.split(osp.sep)
            workspace = osp.sep.join(parts[:-4])
            data_dir = osp.join(workspace, "amira_data_gfx/ABC_stl")
            if not osp.isdir(data_dir):
                raise FileNotFoundError("workspace is missing the amira_data_gfx/ABC_stl subdir")
            return data_dir
        elif osp.isdir(data_dir):
            return data_dir
        else:
            raise FileNotFoundError("data_dir must be a fullpath to data parent directory")

    def _rescale(self, obj, lower_limit, upper_limit):
        """Rescale objects to reasonable sizes (heuristic)

        The STL files do NOT retain their length units, and ABC does not provide it otherwise
        """
        succes = True
        for scene in bpy.data.scenes:
            scene.unit_settings.length_unit = "METERS"

        min_scale = lower_limit / np.min(obj.dimensions)
        max_scale = upper_limit / np.max(obj.dimensions)
        if min_scale > max_scale:
            logger.error("Cannot resolve object scaling")
            logger.warning(",".join((
                f"name = {obj.name}",
                f"dimensions = {obj.dimensions}",
                f"lower_limit = {lower_limit}",
                f"upper_limit = {upper_limit}",
            )))
            return False
        delta = max_scale - min_scale
        scale = min_scale + delta * np.random.rand(1)[0]
        logger.debug(f"randomized scale = {scale}")
        obj.scale *= scale
        return succes

    def import_object(self, object_type=None, filename=None, name=None):
        """Import an ABC STL and assign a material

        Keyword Arguments:
            object_type {string} -- see object_types for options (default: {None = random})
            filename {string} -- filename within object-type directory, kinda of object-id (default: {None = random})
            name {string} -- name for the new object (default: {None = object_type_<random number>})
        """
        if object_type is None:
            object_type = random.sample(self.object_types, 1)[0]
        logger.debug(f"object_type={object_type}")
        dir_path = osp.join(self._parent, self._object_types_map[object_type]["folder"], "STL")
        if filename is None:
            filename = random.sample(os.listdir(dir_path), 1)[0]
        logger.debug(f"filename={filename}")
        file_path = osp.join(dir_path, filename)

        old_names = _get_current_items(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=file_path)
        new_names = _find_new_items(bpy.data.objects, old_names)
        if len(new_names) > 1:
            raise AssertionError("multiple new object names, cannot identify new object")
        temp_name = new_names[0]

        obj_handle = bpy.data.objects.get(temp_name)
        if name is None:
            name = "{}_{}".format(object_type, len(bpy.data.objects))
        obj_handle.name = name

        succes = self._rescale(
            obj_handle,
            self._object_types_map[object_type]["lower_limit"],
            self._object_types_map[object_type]["upper_limit"]
        )
        if not succes:
            bpy.ops.object.select_all(action="DESELECT")
            # bpy.context.scene.objects.active = None
            obj_handle.select_set(True)
            bpy.ops.object.delete()
            return None

        mat = self._material_generator.get_random_material()
        obj_handle.active_material = mat

        return obj_handle


if __name__ == "__main__":

    logger.info("starting __main__")

    step = 0.3
    out_dir = osp.join(os.environ["HOME"], "Desktop", "stl_import_demo")
    try:
        shutil.rmtree(out_dir)
    except FileNotFoundError:
        pass
    os.makedirs(out_dir, exist_ok=True)

    abc_importer = ABCImporter()
    logger.info("instantiated an ABCImporter for STL files")

    object_types = abc_importer.object_types

    bpy.ops.wm.read_homefile(use_empty=True)
    logger.info("opened a blend file")

    _set_viewport_shader()
    logger.info("set shading to MATERIAL")

    abc_importer = ABCImporter(n_materials=10)
    logger.info("instantiated an ABCImporter for STL files")

    for x in range(7):
        for y in range(7):
            obj = abc_importer.import_object()
            if obj is None:
                continue
            obj.location.x = x * step
            obj.location.y = y * step
    out = osp.join(out_dir, "mix.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    logger.info("finished, saved file to {}".format(out))

    for obj_t in object_types:

        bpy.ops.wm.read_homefile(use_empty=True)
        logger.info("opened a blend file")

        _set_viewport_shader()
        logger.info("set shading to MATERIAL")

        abc_importer = ABCImporter(n_materials=10)
        logger.info("instantiated an ABCImporter for STL files")

        for x in range(4):
            for y in range(4):
                obj = abc_importer.import_object(object_type=obj_t)
                if obj is None:
                    continue
                obj.location.x = x * step
                obj.location.y = y * step

        out = osp.join(out_dir, "{}.blend".format(obj_t))
        bpy.ops.wm.save_as_mainfile(filepath=out)
        logger.info("finished, saved file to {}".format(out))
