#!/usr/bin/env python

# Copyright (c) 2016 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


class ABCDataLoader(object):
    """Dataloader for STL files from the ABC dataset

    Returns fullpath to stl file, and a size limits in [m]
    """
    def __init__(self, data_dir=None):
        """Dataloader for ABC dataset

        Args:
            data_dir (str, optional): fullpath to ABC dataset parent directory. Defaults to None.
        """
        self._parent = self._get_abc_parent_dir(data_dir)
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
                folder="Springs", lower_limit=0.005, upper_limit=0.1),
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
                folder="Shafts", lower_limit=0.01, upper_limit=0.2),
            bolt=dict(
                folder="Bolts", lower_limit=0.01, upper_limit=0.1),
            headless_screw=dict(
                folder="HeadlessScrews", lower_limit=0.003, upper_limit=0.05),
            flat_screw=dict(
                folder="Slotted_Flat_Head_Screws", lower_limit=0.003, upper_limit=0.05),
            hex_screw=dict(
                folder="Hex_Head_Screws", lower_limit=0.003, upper_limit=0.05),
            socket_screw=dict(
                folder="Socket_Head_Screws", lower_limit=0.003, upper_limit=0.05),
            nut=dict(
                folder="Nuts", lower_limit=0.01, upper_limit=0.05),
            push_ring=dict(
                folder="Push_Rings", lower_limit=0.0005, upper_limit=0.05),
            retaining_ring=dict(
                folder="Retaining_Rings", lower_limit=0.0005, upper_limit=0.05),
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

    def get_object(self, object_type=None, filename=None):
        """Get a fullpath to a random object STL file"

        Args:
            object_type (string, optional): see object_types for options. Defaults to None (= random).
            filename (string, optional): filename in object-type directory (= object-id). Defaults to None (= random).

        Returns:
            tuple: fullpath to file, object_type, size lower limit [m], size upper limit [m]
                size limits needed for scaling
        """
        if object_type in [None, "random"]:
            object_type = random.sample(self.object_types, 1)[0]
        logger.debug(f"object_type={object_type}")
        dir_path = osp.join(self._parent, self._object_types_map[object_type]["folder"], "STL")
        if filename is None:
            filename = random.sample(os.listdir(dir_path), 1)[0]
        logger.debug(f"filename={filename}")
        file_path = osp.join(dir_path, filename)

        lower_limit = self._object_types_map[object_type]["lower_limit"]
        upper_limit = self._object_types_map[object_type]["upper_limit"]
        return file_path, object_type, lower_limit, upper_limit


# TODO: move object origin to geometric center
class STLImporter(object):
    """Imports an STL file and adds material and physical properties"""

    def __init__(self, material_generator, units="METERS", enable_physics=True, mass=0.01, collision_margin=0.0001):
        self._mat_gen = material_generator
        self._units = units
        self._physhics = enable_physics
        self._mass = mass
        self._collision_margin = collision_margin

    def _set_physical_properties(self, obj, scene=None, mass=None, collision_margin=None):
        """Set required phyisical properties

        Physics simulation is used to drop objects onto scene and place them realistically

        Args:
            obj: object handle
            scene: Scene name, for files with multiple scenes. Defaults to None.
            mass (float, optional): mass in [kg]. Defaults to None.
            collision_margin (float, optional): collision margin in [m]. Defaults to None.
        """
        if not self._physhics:
            logger.debug("Skipping _set_physical_properties")
            return

        if scene is None:
            scene_names = get_collection_item_names(bpy.data.scenes)
            scene = scene_names[0]
            if len(scene_names) > 1:
                logger.warning("found {} scenes, linking object to scene={}".format(len(scene_names), scene))

        _scene = bpy.data.scenes[scene]

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        if _scene.rigidbody_world is None:
            logger.debug("adding a rigidbody_world to scene, i.e. a RigidBodyWorld collection")
            bpy.ops.rigidbody.world_add()

        bpy.ops.rigidbody.object_add()
        if obj.rigid_body is None:
            raise AssertionError("Failed to link object to rigidbody_world collection")

        if mass is None:
            mass = self._mass
        if collision_margin is None:
            collision_margin = self._collision_margin
        obj.rigid_body.type = "ACTIVE"
        obj.rigid_body.use_margin = True
        obj.rigid_body.mass = mass
        obj.rigid_body.collision_margin = collision_margin

    def _set_scene_units(self, scene=None):
        if scene is None:
            for scene in bpy.data.scenes:
                scene.unit_settings.length_unit = self._units
        else:
            if isinstance(scene, str):
                try:
                    bpy.data.scenes[scene].unit_settings.length_unit = self._units
                except KeyError as err:
                    logger.critical(f"{scene} is not a valid scene name")
                    raise err
            else:
                try:
                    scene.unit_settings.length_unit = self._units
                except Exception as err:
                    raise err

    @staticmethod
    def _random_rescale(obj, lower_limit, upper_limit):
        """Rescale object to a reasonable size

        (ABC) STL files do NOT retain length units

        Args:
            obj: blender object handle
            lower_limit (float): lower size limit [m]
            upper_limit (float): upper size limit [m]

        Returns:
            bool: success
        """
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

    def import_object(self, stl_fullpath, name, scale=None, size_limits=None, mass=None, collision_margin=None):
        """Import an STL file and assign material and physical properties

        Args:
            stl_fullpath (string): fullpath to STL file.
            name (string): name for the new object.
            scale (float): scale to resize object. Overrides size_limits. Defaults to None.
            size_limits (tuple of floats): lower and upper size limits, for random rescaling. Defaults to None.
            mass (float, optional): mass [kg]. Defaults to None; uses class instance config
            collision_margin (float, optional): collision margin [m]. Defaults to None; uses class instance config

        Returns:
            bpy_types.Object: a handle to the generated object
        """
        old_names = get_collection_item_names(bpy.data.objects)
        bpy.ops.import_mesh.stl(filepath=stl_fullpath)
        # rename
        new_names = find_new_items(bpy.data.objects, old_names)
        temp_name = new_names.pop()
        obj = bpy.data.objects.get(temp_name)
        obj.name = name

        rescale_success = True
        if isinstance(scale, (int, float)):
            obj.scale *= scale
        elif scale is None:
            if size_limits is None:
                logger.warning("both scale and size_limits are None, object scale left unchanged")

        if size_limits is not None:
            lower_limit, upper_limit = size_limits
            rescale_success = self._random_rescale(obj, lower_limit, upper_limit)

        obj.active_material = self._mat_gen.get_material()

        self._set_physical_properties(obj)

        return obj, rescale_success


class ABCImporter(object):
    """Import ABC STL into blender session and assign material and physical properties"""
    def __init__(self, data_dir=None, n_materials=3, mass=0.01, collision_margin=0.0001):
        """Configuration

        Args:
            data_dir (str, optional): fullpath to ABC dataset parent directory. Defaults to None.
            n_materials (int, optional): Number of random materials to generate. Defaults to 3.
            mass (float, optional): mass in [kg]. Defaults to 0.01.
            collision_margin (float, optional): collision_margin in [m]. Defaults to 0.0001.
            Physics simulation params are necessary for randomized object placement.
        """
        self._dataloader = ABCDataLoader(data_dir=data_dir)
        material_generator = MetallicMaterialGenerator()
        material_generator.make_random_material(n=n_materials)
        self._stl_importer = STLImporter(
            material_generator, units="METERS", enable_physics=True, mass=mass, collision_margin=collision_margin)

    @property
    def object_types(self):
        return self._dataloader.object_types

    def import_object(self, object_type=None, filename=None, name=None, mass=None, collision_margin=None):
        """Import an ABC STL and assign a material

        Args:
            object_type (string, optional): see object_types for options. Defaults to None (= random).
            filename (string, optional): filename in object-type directory (= object-id). Defaults to None (= random).
            name (string, optional): name for the new object. Defaults to None (= object_type_<random number>).
            mass (float, optional): mass [kg]. Defaults to None; uses class instance config
            collision_margin (float, optional): collision margin [m]. Defaults to None; uses class instance config

        Returns:
            bpy_types.Object: a handle to the generated object
        """
        stl_fullpath, object_type, lower_limit, upper_limit = self._dataloader.get_object(
            object_type=object_type, filename=filename)

        if name is None:
            name = "{}_{}".format(object_type, len(bpy.data.objects))

        obj_handle, rescale_success = self._stl_importer.import_object(
            stl_fullpath, name, size_limits=(lower_limit, upper_limit), mass=mass, collision_margin=collision_margin)

        if not rescale_success:
            bpy.ops.object.select_all(action="DESELECT")
            # bpy.context.scene.objects.active = None
            obj_handle.select_set(True)
            bpy.ops.object.delete()
            return None, None

        return obj_handle, object_type


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
            obj, _ = abc_importer.import_object()
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
                obj, _ = abc_importer.import_object(object_type=obj_t)
                if obj is None:
                    continue
                obj.location.x = x * step
                obj.location.y = y * step

        out = osp.join(out_dir, "{}.blend".format(obj_t))
        bpy.ops.wm.save_as_mainfile(filepath=out)
        logger.info("finished, saved file to {}".format(out))
