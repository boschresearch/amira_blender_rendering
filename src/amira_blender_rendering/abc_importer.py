#!/usr/bin/env python

import os
import os.path as osp
import shutil
import random
import numpy as np

import bpy

import amira_blender_rendering.utils.logging as log_utils
from amira_blender_rendering.utils.blender import get_collection_item_names, find_new_items
from amira_blender_rendering.utils.material import MetallicMaterialGenerator, set_viewport_shader

logger = log_utils.get_logger()


# TODO: separate into an STL-importer, and a ABC data-loader
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

        Returns
            list of strings, labels of supported object types
        """
        return sorted(key for key in self._object_types_map)

    def _get_object_types_map(self):
        object_types_map = dict(
            bearings=dict(
                folder="Bearings", lower_limit=0.01, upper_limit=0.1),
            sprocket=dict(
                folder="Sprockets", lower_limit=0.01, upper_limit=0.15),
            spring=dict(
                folder="Springs", lower_limit=0.01, upper_limit=0.2),
            flange=dict(
                folder="Unthreaded_Flanges", lower_limit=0.01, upper_limit=0.2),
            bracket=dict(
                folder="Brackets", lower_limit=0.01, upper_limit=0.3),
            collet=dict(
                folder="Collets", lower_limit=0.01, upper_limit=0.1),
            pipe=dict(
                folder="Pipes", lower_limit=0.01, upper_limit=0.4),
            pipe_fitting=dict(
                folder="Pipe_Fittings", lower_limit=0.01, upper_limit=0.15),
            pipe_joint=dict(
                folder="Pipe_Joints", lower_limit=0.01, upper_limit=0.1),
            bushing=dict(
                folder="Bushing", lower_limit=0.01, upper_limit=0.15),
            roller=dict(
                folder="Rollers", lower_limit=0.01, upper_limit=0.1),
            busing_liner=dict(
                folder="Bushing_Damping_Liners", lower_limit=0.01, upper_limit=0.15),
            shaft=dict(
                folder="Shafts", lower_limit=0.01, upper_limit=0.3),
            bolt=dict(
                folder="Bolts", lower_limit=0.01, upper_limit=0.1),
            headless_screw=dict(
                folder="HeadlessScrews", lower_limit=0.01, upper_limit=0.05),
            flat_screw=dict(
                folder="Slotted_Flat_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            hex_screw=dict(
                folder="Hex_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            socket_screw=dict(
                folder="Socket_Head_Screws", lower_limit=0.01, upper_limit=0.05),
            nut=dict(
                folder="Nuts", lower_limit=0.01, upper_limit=0.05),
            push_ring=dict(
                folder="Push_Rings", lower_limit=0.01, upper_limit=0.05),
            retaining_ring=dict(
                folder="Retaining_Rings", lower_limit=0.01, upper_limit=0.05),
            washer=dict(
                folder="Washers", lower_limit=0.01, upper_limit=0.05),
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
        """Get and check data path

        Args:
            data_dir (string, None): string = path to ABC-STL data directory, None = resolve form environment variable

        Raises:
            KeyError: if the user relies on the AMIRA_DATA_GFX environemnt variable, but forgets to set it
            FileNotFoundError: if the ABB-STL directory cannot be found

        Returns:
            string: path to ABC-STL data directory
        """
        if data_dir is None:
            # resolve from environment variable

            try:
                data_parent = os.environ["AMIRA_DATA_GFX"]
            except KeyError as err:
                logger.critical(
                    "Please set an environment variable AMIRA_DATA_GFX to parent directory of ABC_stl directory")
                raise err

            data_dir = osp.join(data_parent, "ABC_stl")
            if not osp.isdir(data_dir):
                raise FileNotFoundError("excpecitng the parent directory to contain an ABC_stl subdir")

            return data_dir

        elif osp.isdir(data_dir):
            # hopefully user specified correct path to "ABC_stl" directory
            return data_dir

        else:
            raise FileNotFoundError("data_dir must be a fullpath to ABC-STL data parent directory")

    def _rescale(self, obj, lower_limit, upper_limit):
        """Rescale objects to reasonable sizes (heuristic)

        The STL files do NOT retain their length units, and ABC does not provide it otherwise
        """
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
        return True

    def import_object(self, object_type=None, filename=None, name=None):
        """Import an ABC STL and assign a material

        Args:
            object_type (string, optional): see object_types for options. Defaults to None (= random).
            filename (string, optional): filename in object-type directory (= object-id). Defaults to None (= random).
            name (string, optional): name for the new object. Defaults to None (= object_type_<random number>).

        Raises:
            AssertionError: [description]

        Returns:
            bpy_types.Object: a handle to the generated object
        """
        if object_type is None:
            object_type = random.sample(self.object_types, 1)[0]
        logger.debug(f"object_type={object_type}")
        dir_path = osp.join(self._parent, self._object_types_map[object_type]["folder"], "STL")
        if filename is None:
            filename = random.sample(os.listdir(dir_path), 1)[0]
        logger.debug(f"filename={filename}")
        file_path = osp.join(dir_path, filename)

        old_names = get_collection_item_names(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=file_path)
        new_names = find_new_items(bpy.data.objects, old_names)
        if len(new_names) > 1:
            raise AssertionError("multiple new object names, cannot identify new object")
        temp_name = new_names.pop()

        obj_handle = bpy.data.objects.get(temp_name)
        if name is None:
            name = "{}_{}".format(object_type, len(bpy.data.objects))
        obj_handle.name = name

        success = self._rescale(
            obj_handle,
            self._object_types_map[object_type]["lower_limit"],
            self._object_types_map[object_type]["upper_limit"]
        )
        if not success:
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

    set_viewport_shader()
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

        set_viewport_shader()
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
