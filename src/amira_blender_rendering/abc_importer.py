import os
import os.path as osp
import random
import numpy as np

import bpy

# import utils.logging.get_logger as get_logger
# from utils.logging import get_logger
from amira_blender_rendering.utils.logging import get_logger

logger = get_logger()


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


class MetallicMaterialGenerator(object):
    """Generate randomized metallic materials"""
    def __init__(self):
        self._rgb_lower_limits = (0.9, 0.7, 0.6)
        self._shift_to_white = 2.0
        self._max_roughness = 0.4
        self._max_texture_scale = 0.7
        self._max_texture_detail = 10.0
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
            bearings="Bearings",
            sprocket="Sprockets",
            spring="Springs",
            flange="Unthreaded_Flanges",
            bracket="Brackets",
            collet="Collets",
            pipe="Pipes",
            pipe_fitting="Pipe_Fittings",
            pipe_joint="Pipe_Joints",
            bushing="Bushing",
            roller="Rollers",
            busing_liner="Bushing_Damping_Liners",
            shaft="Shafts",
            bolt="Bolts",
            headless_screw="HeadlessScrews",
            flat_screw="Slotted_Flat_Head_Screws",
            hex_screw="Hex_Head_Screws",
            socket_screw="Socket_Head_Screws",
            nut="Nuts",
            push_ring="Push_Rings",
            retaining_ring="Retaining_Rings",
            washer="Washers",
        )

        missing = 0
        verified_types = dict()
        for obj in object_types_map:
            if osp.isdir(osp.join(self._parent, object_types_map[obj])):
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
        dir_path = osp.join(self._parent, self._object_types_map[object_type], "STL")
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

        mat = self._material_generator.get_random_material()
        obj_handle.active_material = mat

        return obj_handle


if __name__ == "__main__":

    import logging
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(
        logging.Formatter("[{}] {}:{} | {}".format(
            "%(levelname)s",
            "%(filename)s",
            "%(lineno)d",
            "%(message)s",
        ),))
    logger.addHandler(stream_handler)

    logger.info("starting __main__")

    bpy.ops.wm.read_homefile(use_empty=True)
    logger.info("opened a blend file")

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = "MATERIAL"
    logger.info("set shading to MATERIAL")

    abc_importer = ABCImporter(n_materials=10)
    logger.info("instantiated an ABCImporter for STL files")

    step = 10
    for x in range(6):
        for y in range(6):
            obj = abc_importer.import_object()
            obj.location.x = x * step
            obj.location.y = y * step

    out = osp.join(os.environ["HOME"], "Desktop", "stl_import_demo.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    logger.info("finished, saved file to {}".format(out))
