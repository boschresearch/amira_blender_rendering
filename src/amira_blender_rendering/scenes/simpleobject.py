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

# blender
import bpy
import os
from mathutils import Vector, Matrix
import pathlib
from math import ceil, log
import random
import numpy as np

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.interfaces as interfaces

_scene_name = 'SimpleObject'


@abr_scenes.register(name=_scene_name, type='config')
class SimpleObjectConfiguration(abr_scenes.BaseConfiguration):
    def __init__(self):
        super(SimpleObjectConfiguration, self).__init__()

        # scene specific configuration
        # let's be able to specify environment textures
        self.add_param('scene_setup.environment_textures',
                       '$AMIRA_DATASETS/OpenImagesV4/Images',
                       'Path to background images / environment textures')
        self.add_param('scenario_setup.target_object', 'Tool.Cap', 'Define single target object to render')
        self.add_param('scenario_setup.object_material', 'metal', 'Select object material ["plastic", "metal"]')


@abr_scenes.register(name=_scene_name, type='scene')
class SimpleObject(interfaces.ABRScene):
    """Simple scene with a single object in which we have three point lighting and can set
    some background image.
    """
    def __init__(self, **kwargs):
        super(SimpleObject, self).__init__()
        self.logger = get_logger()

        # we make use of the RenderManager
        self.renderman = abr_scenes.RenderManager()

        # get the configuration, if one was passed in
        self.config = kwargs.get('config', SimpleObjectConfiguration())

        # determine if we are rendering in multiview mode
        self.render_mode = kwargs.get('render_mode', 'default')
        if not self.render_mode == 'default':
            self.logger.warn(f'{self.__class__} scene supports only "default" render mode. Falling back to "default"')
            self.render_mode = 'default'

        # we might have to post-process the configuration
        self.postprocess_config()

        # set up directory information that will be used
        self.setup_dirinfo()

        # set up anything that we need for the scene before doing anything else.
        # For instance, removing all default objects
        self.setup_scene()

        # now that we have setup the scene, let's set up the render manager
        self.renderman.setup_renderer(
            self.config.render_setup.integrator,
            self.config.render_setup.denoising,
            self.config.render_setup.samples,
            self.config.render_setup.motion_blur)

        # setup environment texture information
        self.setup_environment_textures()

        # setup the camera that we wish to use
        self.setup_cameras()

        # setup render / output settings
        self.setup_render_output()

        # setup the object that we want to render
        self.setup_objects()

        # finally, let's setup the compositor
        self.setup_compositor()

    def postprocess_config(self):
        # in default mode (i.e., single view), image_count control the number of images (hence scene) to render
        self.config.dataset.view_count = 1
        self.config.dataset.scene_count = self.config.dataset.image_count

        # log info
        self.logger.info(f'{self.__class__} scene does not allow for occlusions --> Object always visible')
        self.config.render_setup.allow_occlusions = False
        self.logger.info(f'{self.__class__} scene does not support multiview rendering.')

        # convert (PLY and blend) scaling factors from str to list of floats
        def _convert_scaling(key: str, config):
            """
            Convert scaling factors from string to (list of) floats
            
            Args:
                key(str): string to identify prescribed scaling
                config(Configuration): object to modify

            Return:
                none: directly update given "config" object
            """
            if key not in config:
                return

            for part in config[key]:
                vs = config[key][part]
                # split strip and make numeric
                vs = [v.strip() for v in vs.split(',')]
                vs = [float(v) for v in vs]
                # if single value given, apply to all axis
                if len(vs) == 1:
                    vs *= 3
                config[key][part] = vs

        _convert_scaling('ply_scale', self.config.parts)
        _convert_scaling('blend_scale', self.config.parts)

    def setup_render_output(self):
        # setup render output dimensions. This is not set for a specific camera,
        # but in renders render environment
        # first set the resolution if it was specified in the configuration
        if (self.config.camera_info.width > 0) and (self.config.camera_info.height > 0):
            bpy.context.scene.render.resolution_x = self.config.camera_info.width
            bpy.context.scene.render.resolution_y = self.config.camera_info.height

        # Setting the resolution can have an impact on the intrinsics that were
        # used for rendering. Hence, we will store the effective intrinsics
        # alongside.
        # First, get the effective values
        effective_intrinsic = camera_utils.get_intrinsics(bpy.context.scene, self.cam)
        # Second, backup original intrinsics, and store effective intrinsics
        if self.config.camera_info.intrinsic is not None:
            self.config.camera_info.original_intrinsic = self.config.camera_info.intrinsic
        else:
            self.config.camera_info.original_intrinsic = ''
        self.config.camera_info.intrinsic = list(effective_intrinsic)

    def setup_dirinfo(self):
        """Setup directory information."""
        # For this simple scene, there is just one dirinfo required
        self.dirinfo = build_directory_info(self.config.dataset.base_path)

    def setup_scene(self):
        """Setup the scene. """
        # first, delete everything in the scene
        blnd.clear_all_objects()

        # now we also setup lighting. We use a simple three point lighting in
        # this simple scene
        self.lighting = abr_scenes.ThreePointLighting()

    def setup_cameras(self):
        """Setup camera, and place at a default location"""
        # get scene
        scene = bpy.context.scene

        # add camera, update with calibration data, and make it active for the scene
        bpy.ops.object.add(type='CAMERA', location=(0.66, -0.66, 0.5))
        self.cam_obj = bpy.context.object
        self.cam = self.cam_obj.data
        camera_utils.set_camera_info(scene, self.cam, self.config.camera_info)

        # re-set camera and set rendering size
        bpy.context.scene.camera = self.cam_obj
        if (self.config.camera_info.width > 0) and (self.config.camera_info.height > 0):
            bpy.context.scene.render.resolution_x = self.config.camera_info.width
            bpy.context.scene.render.resolution_y = self.config.camera_info.height

        # look at center
        blnd.look_at(self.cam_obj, Vector((0.0, 0.0, 0.0)))

        # get effective extrinsics
        effective_intrinsic = camera_utils.get_intrinsics(scene, self.cam)
        # store in configuration (and backup original values)
        if self.config.camera_info.intrinsic is not None:
            self.config.camera_info.original_intrinsic = self.config.camera_info.intrinsic
        else:
            self.config.camera_info.original_intrinsic = ''
        self.config.camera_info.intrinsic = list(effective_intrinsic)

    def setup_objects(self):
        # the order of what's done is important. first import and setup the
        # object and its material, then rescale it. otherwise, values from
        # shader nodes might not reflect the correct sizes (the metal-tool-cap
        # material depends on an empty that is placed on top of the object.
        # scaling the empty will scale the texture)
        self._import_object()
        self._setup_material()

        # we also need to create a dictionary with the object for the compositor
        # to do its job, as well as the annotation generation
        self.objs = list()
        self.objs.append({
            'id_mask': '_0_0',                  # the format of the masks is usually _modelid_objectid
            'object_class_name': 'Tool.Cap',    # model name is hardcoded here
            'object_class_id': 0,               # we only have one model type, so id = 0
            'object_id': 0,                     # we only have this single instance, so id = 0
            'bpy': self.obj,                    # also add reference to the blender object
            'visible': True})                   # visibility information

    def setup_compositor(self):
        # we let renderman handle the compositor. For this, we need to pass in a
        # list of objects
        self.renderman.setup_compositor(self.objs, color_depth=self.config.render_setup.color_depth)

    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)

    def _rescale_object(self, scale):
        try:
            self.obj.scale = Vector(self.config.parts[scale][self.config.scenario_setup.target_object])
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)
        except KeyError:
            # log and keep going
            self.logger.info(f'No scale for obj {self.obj.name} given. Skipping!')

    def _import_object(self):
        """Import the mesh of the cap from a ply file."""
        bpy.ops.object.select_all(action='DESELECT')
        class_name = expandpath(self.config.scenario_setup.target_object)
        blendfile = expandpath(self.config.parts[class_name], check_file=False)
        # try blender file
        if os.path.exists(blendfile):
            try:
                bpy_obj_name = self.config.parts['name'][class_name]
            except KeyError:
                bpy_obj_name = class_name
            blnd.append_object(blendfile, bpy_obj_name)
            new_obj = bpy.data.objects[bpy_obj_name]
            scale_type = 'blend_scale'
        # if none given try ply
        else:
            ply_path = expandpath(self.config.parts.ply[class_name], check_file=True)
            bpy.ops.import_mesh.ply(filepath=ply_path)
            new_obj = bpy.context.object
            scale_type = 'ply_scale'

        new_obj.name = class_name
        self.obj = new_obj
        self._rescale_object(scale_type)

    def _setup_material(self):
        """Setup object material"""
        available_materials = {
            'metal': abr_nodes.material_metal_tool_cap,
            'plastic': abr_nodes.material_3Dprinted_plastic
        }

        material = self.config.scenario_setup.object_material.lower()
        if material not in available_materials:
            raise ValueError(f'Requested material "{material}" is not supported')

        # make sure cap is selected
        blnd.select_object(self.obj.name)

        # remove any material that's currently assigned to the object and then
        # setup the metal for the cap
        blnd.remove_material_nodes(self.obj)
        blnd.clear_orphaned_materials()

        # add default material and setup nodes (without specifying empty, to get
        # it created automatically)
        self.obj_mat = blnd.add_default_material(self.obj)
        available_materials[material].setup_material(self.obj_mat)

    def randomize_object_transforms(self):
        """Set an arbitrary location and rotation for the object"""

        ok = False
        while not ok:
            # random R,t
            self.obj.location = Vector((1.0 * np.random.rand(3) - 0.5))
            self.obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            self._update_scene()

            # Test if object is still visible. That is, none of the vertices
            # should lie outside the visible pixel-space
            ok = self._test_obj_visibility()

    def randomize_environment_texture(self):
        # set some environment texture, randomize, and render
        env_txt_filepath = expandpath(random.choice(self.environment_textures))
        self.renderman.set_environment_texture(env_txt_filepath)

    def set_pose(self, pose):
        """
        Set a specific pose for the object.
        Alternative method to randomize(), in order to render given poses.

        Args:
            pose(dict): dict with rotation and translation
                {
                    'R': rotation(np.array(3)), rotation matrix
                    't': translation(np.array(3,)), translation vector expressed in meters
                }

        Raise:
            ValueError: if pose is not valid, i.e., object outside the scene
        """
        # get desired rototranslation (this is in OpenGL coordinate system) in camera frame
        world_pose = abr_geom.get_world_to_object_transform(pose, self.cam_obj)

        # set pose
        self.obj.location = Vector((world_pose['t']))
        self.obj.rotation_euler = Matrix(world_pose['R']).to_euler()

        # update the scene. unfortunately it doesn't always work to just set
        # the location of the object without recomputing the dependency
        # graph
        self._update_scene()

        # Test if object is still visible. That is, none of the vertices
        # should lie outside the visible pixel-space
        if not self._test_obj_visibility():
            raise ValueError('Given pose is lying outside the scene')

    def _test_obj_visibility(self):
        return abr_geom.test_visibility(
            self.obj,
            self.cam_obj,
            self.config.camera_info.width,
            self.config.camera_info.height)

    def _update_scene(self):
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

    def dump_config(self):
        pathlib.Path(self.dirinfo.base_path).mkdir(parents=True, exist_ok=True)
        dump_config(self.config, self.dirinfo.base_path)

    def generate_dataset(self):
        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        format_width = int(ceil(log(image_count, 10)))

        i = 0
        while i < self.config.dataset.image_count:
            # generate render filename: adhere to naming convention
            base_filename = f"s{i:0{format_width}}_v0"

            # randomize environment and object transform
            self.randomize_environment_texture()
            self.randomize_object_transforms()

            # setup render managers' path specification
            self.renderman.setup_pathspec(self.dirinfo, base_filename, self.objs)

            # render the image
            self.renderman.render()

            # try to postprocess. This might fail, in which case we should
            # attempt to re-render the scene with different randomization
            try:
                self.renderman.postprocess(
                    self.dirinfo,
                    base_filename,
                    bpy.context.scene.camera,
                    self.objs,
                    self.config.camera_info.zeroing,
                    postprocess_config=self.config.postprocess)
            except ValueError:
                self.logger.warn("ValueError during post-processing, re-generating image index {i}")
            else:
                i = i + 1

        return True

    def teardown(self):
        pass
