#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
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

"""
This file implements generation of datasets for workstation scenarios. The file
depends on a suitable workstation scenarion blender file such as
worstationscenarios.blend.
"""

import bpy
import os
# import sys
import pathlib
from mathutils import Vector
# import time
import numpy as np
import random
from math import ceil, log

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.utils.logging import get_logger
# from amira_blender_rendering.datastructures import Configuration, flatten
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.interfaces as interfaces
from amira_blender_rendering.abc_importer import ABCImporter
from amira_blender_rendering.utils.annotation import ObjectBookkeeper


class WorkstationScenariosConfiguration(abr_scenes.BaseConfiguration):
    """This class specifies all configuration options for WorkstationScenarios"""

    def __init__(self):
        super(WorkstationScenariosConfiguration, self).__init__()

        # specific scene configuration
        self.add_param('scene_setup.blend_file', '$AMIRA_DATA_GFX/modeling/workstation_scenarios.blend',
                       'Path to .blend file with modeled scene')
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images',
                       'Path to background images / environment textures')
        self.add_param('scene_setup.cameras', ['CameraLeft', 'Camera', 'CameraRight'], 'Cameras to render')
        self.add_param('scene_setup.forward_frames', 15, 'Number of frames in physics forward-simulation')

        # specific parts configuration. This is just a dummy entry for purposes
        # of demonstration and help message generation
        # self.add_param('parts.example_dummy', '/path/to/example_dummy.blend', 'Path to additional blender files containing invidual parts. Format must be partname = /path/to/blendfile.blend')
        # self.add_param('parts.ply.example_dummy', '/path/to/example_dummy.ply', 'Path to PLY files containing part "example_dummy". Format must be ply.partname = /path/to/blendfile.ply')
        # self.add_param('parts.ply_scale.example_dummy', [1.0, 1.0, 1.0], 'Scaling factor in X, Y, Z dimensions of part "example_dummy". Format must be a list of 3 floats.')

        # specific scenario configuration
        self.add_param('scenario_setup.scenario', 0, 'Scenario to render')
        self.add_param('scenario_setup.target_objects', [], 'List of all target objects to drop in environment')
        self.add_param('scenario_setup.abc_objects', [], 'List of all ABC-Dataset objects to drop in environment')
        self.add_param('scenario_setup.n_abc_colors', 3, 'Number of random metallic materials to generate')
        # HINT: these object lists above are parsed as strings, later on split with "," separator


class WorkstationScenarios(interfaces.ABRScene):
    """base class for all workstation scenarios"""

    def __init__(self, **kwargs):
        super(WorkstationScenarios, self).__init__()
        self.logger = get_logger()

        # we do composition here, not inheritance anymore because it is too
        # limiting in its capabilities. Using a render manager is a better way
        # to handle compositor nodes
        self.renderman = abr_scenes.RenderManager()

        # extract configuration, then build and activate a split config
        self.config = kwargs.get('config', WorkstationScenariosConfiguration())
        if self.config.dataset.scene_type.lower() != 'WorkstationScenarios'.lower():
            raise RuntimeError(
                f"Invalid configuration of scene type {self.config.dataset.scene_type} for class WorkstationScenarios")
        # we might have to post-process the configuration
        self.postprocess_config()

        # setup directory information for each camera
        self.setup_dirinfo()

        # setup the scene, i.e. load it from file
        self.setup_scene()

        # setup the renderer. do this _AFTER_ the file was loaded during
        # setup_scene(), because otherwise the information will be taken from
        # the file, and changes made by setup_renderer ignored
        self.renderman.setup_renderer(
            self.config.render_setup.integrator,
            self.config.render_setup.denoising,
            self.config.render_setup.samples)

        # grab environment textures
        self.setup_environment_textures()

        # setup all camera information according to the configuration
        self.setup_cameras()

        # setup global render output configuration
        self.setup_render_output()

        # populate the scene with objects
        self.setup_objects()

        # finally, setup the compositor
        self.setup_compositor()

    def postprocess_config(self):
        # convert all scaling factors from str to list of floats
        if 'ply_scale' not in self.config.parts:
            return

        for part in self.config.parts.ply_scale:
            vs = self.config.parts.ply_scale[part]
            vs = [v.strip() for v in vs.split(',')]
            vs = [float(v) for v in vs]
            self.config.parts.ply_scale[part] = vs

    def setup_dirinfo(self):
        """Setup directory information for all cameras.

        This will be required to setup all path information in compositor nodes
        """
        # compute directory information for each of the cameras
        self.dirinfos = list()
        for cam in self.config.scene_setup.cameras:
            # DEPRECATED:
            # paths are set up as: base_path + Scenario## + CameraName
            # camera_base_path = f"{self.config.dataset.base_path}-Scenario{self.config.scenario_setup.scenario:02}-{cam}"

            # NEW:
            # paths are set up as: base_path + CameraName
            camera_base_path = f"{self.config.dataset.base_path}-{cam}"
            dirinfo = build_directory_info(camera_base_path)
            self.dirinfos.append(dirinfo)

    def setup_scene(self):
        """Set up the entire scene.

        Here, we simply load the main blender file from disk.
        """
        bpy.ops.wm.open_mainfile(filepath=expandpath(self.config.scene_setup.blend_file))
        # we need to hide all dropboxes and dropzones in the viewport, otherwise
        # occlusion testing will not work, because blender's ray_cast method
        # returns hits no empties!
        self.logger.info("Hiding all dropzones from viewport")
        bpy.data.collections['Dropzones'].hide_viewport = True

    def setup_render_output(self):
        """setup render output dimensions. This is not set for a specific camera,
        but in renders render environment.

        Note that this should be called _after_ cameras were set up, because
        their setup might influence these values.
        """

        # first set the resolution if it was specified in the configuration
        if (self.config.camera_info.width > 0) and (self.config.camera_info.height > 0):
            bpy.context.scene.render.resolution_x = self.config.camera_info.width
            bpy.context.scene.render.resolution_y = self.config.camera_info.height

        # Setting the resolution can have an impact on the calibration matrix
        # that was used for rendering. Hence, we will store the effective
        # calibration matrix K alongside. Because we use identical cameras, we
        # can extract this from one of the cameras
        self.get_effective_intrinsics()

    def get_effective_intrinsics(self):
        """Get the effective intrinsics that were used during rendering.

        This function will copy original values for intrinsic, sensor_width, and
        focal_length, and fov, to the configuration an prepend them with 'original_'. This
        way, they are available in the dataset later on
        """

        cam_str = self.config.scene_setup.cameras[0]
        cam_name = f"{cam_str}.{self.config.scenario_setup.scenario:03}"
        cam = bpy.data.objects[cam_name].data

        # get the effective intrinsics
        effective_intrinsic = camera_utils.get_intrinsics(bpy.context.scene, cam)
        # store in configuration (and backup original values)
        if self.config.camera_info.intrinsic is not None:
            self.config.camera_info.original_intrinsic = self.config.camera_info.intrinsic
        else:
            self.config.camera_info.original_intrinsic = ''
        self.config.camera_info.intrinsic = list(effective_intrinsic)

    def setup_cameras(self):
        """Set up all cameras.

        Note that this does not select a camera for which to render. This will
        be selected elsewhere.
        """
        scene = bpy.context.scene
        for cam in self.config.scene_setup.cameras:
            # first get the camera name. this depends on the scene (blend file)
            # and is of the format CameraName.XXX, where XXX is a number with
            # leading zeros
            cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
            # select the camera. Blender often operates on the active object, to
            # make sure that this happens here, we select it
            blnd.select_object(cam_name)
            # modify camera according to the intrinsics
            blender_camera = bpy.data.objects[cam_name].data
            # set the calibration matrix
            camera_utils.set_camera_info(scene, blender_camera, self.config.camera_info)

    def setup_objects(self):
        """This method populates the scene with objects.

        Object types and number of objects will be taken from the configuration.
        The format to specify objects is
            ObjectType:Number
        where ObjectType should be the name of an object that exists in the
        blender file, and number indicates how often the object shall be
        duplicated.
        """
        rgb_shape = (self.config.camera_info.height, self.config.camera_info.width, 3)
        # let's start with an empty list
        self.objs = []
        self._obk = ObjectBookkeeper()

        # extract all objects from the configuration. An object has a certain
        # type, as well as an own id. this information is storeed in the objs
        # list, which contains a dict. The dict contains the following keys:
        #       id_mask             used for mask computation, computed below
        #       object_class_name   type-name of the object
        #       object_class_id     model type ID (simply incremental numbers)
        #       object_id           instance ID of the object
        #       bpy                 blender object reference
        for class_id, obj_spec in enumerate(self.config.scenario_setup.target_objects):
            class_str, obj_count = obj_spec.split(':')

            # here we distinguish if we copy a part from the proto objects
            # within a scene, or if we have to load it from file
            is_proto_object = not class_str.startswith('parts.')
            if not is_proto_object:
                # split off the prefix for all files that we load from blender
                class_str = class_str[6:]

            # TODO: file loading happens only very late in this loop. This might
            #       be an issue for large object counts and could be changed to
            #       load-once copy-often.
            for j in range(int(obj_count)):
                # First, deselect everything
                bpy.ops.object.select_all(action='DESELECT')
                if is_proto_object:
                    # duplicate proto-object
                    blnd.select_object(class_str)
                    bpy.ops.object.duplicate()
                    new_obj = bpy.context.object
                else:
                    # we need to load this object from file. This could be
                    # either a blender file, or a PLY file
                    blendfile = expandpath(self.config.parts[class_str], check_file=False)
                    if os.path.exists(blendfile):
                        # this is a blender file, so we should load it
                        # we can now load the object into blender
                        blnd.append_object(blendfile, class_str)
                        # NOTE: bpy.context.object is **not** the object that we are
                        # interested in here! We need to select it via original name
                        # first, then we rename it to be able to select additional
                        # objects later on
                        new_obj = bpy.data.objects[class_str]
                        new_obj.name = f'{class_str}.{j:03d}'
                    else:
                        # no blender file given, so we will load the PLY file
                        ply_path = expandpath(self.config.parts.ply[class_str], check_file=True)
                        bpy.ops.import_mesh.ply(filepath=ply_path)
                        # here we can use bpy.context.object!
                        new_obj = bpy.context.object
                        new_obj.name = f'{class_str}.{j:03d}'

                self._obk.add(class_str)

                # append all information
                self.objs.append({
                    'id_mask': '',
                    'object_class_name': class_str,
                    'object_class_id': class_id,
                    'object_id': j,
                    'bpy': new_obj,
                    'dimensions': rgb_shape
                })

        # Adding ABC objects
        abc_objects = self.config.scenario_setup.abc_objects
        if abc_objects == list():
            self.logger.info("Config file does NOT include ABC-Dataset objects")
        else:
            n_materials = int(self.config.scenario_setup.n_abc_colors)
            self.logger.info(f"making {n_materials} random metallic materials")
            abc_importer = ABCImporter(n_materials=n_materials)

        for class_id, obj_spec in enumerate(abc_objects):
            _class_str, obj_count = obj_spec.split(':')

            for j in range(int(obj_count)):
                bpy.ops.object.select_all(action='DESELECT')

                obj_handle, class_str = abc_importer.import_object(_class_str)

                if obj_handle is None:
                    continue

                self._obk.add(class_str)

                self.objs.append({
                    'id_mask': '',
                    'object_class_name': class_str,
                    'object_class_id': self._obk[class_str]["id"],
                    'object_id': self._obk[class_str]["instances"] - 1,
                    'bpy': obj_handle,
                    'dimensions': rgb_shape
                })

        # build masks id for compositor of the format _N_M, where N is the model
        # id, and M is the object id
        w_class = ceil(log(len(self._obk)))  # format width for number of model types
        for i, obj in enumerate(self.objs):
            obj_id, class_id, class_str = obj["object_id"], obj['object_class_id'], obj["object_class_name"]
            n_class_instances = self._obk[class_str]["instances"]
            w_obj = ceil(log(n_class_instances))  # format width for number of objects of same model
            id_mask = f"_{class_id:0{w_class}}_{obj_id:0{w_obj}}"
            obj['id_mask'] = id_mask

    def setup_compositor(self):
        self.renderman.setup_compositor(self.objs)

    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)

    def randomize_object_transforms(self):
        """move all objects to random locations within their scenario dropzone,
        and rotate them."""

        # we need #objects * (3 + 3)  many random numbers, so let's just grab them all
        # at once
        rnd = np.random.uniform(size=(len(self.objs), 3))
        rnd_rot = np.random.rand(len(self.objs), 3)

        # now, move each object to a random location (uniformly distributed) in
        # the scenario-dropzone. The location of a drop box is its centroid (as
        # long as this was not modified within blender). The scale is the scale
        # along the axis in one direction, i.e. the full extend along this
        # direction is 2 * scale.
        dropbox = f"Dropbox.{self.config.scenario_setup.scenario:03}"
        drop_location = bpy.data.objects[dropbox].location
        drop_scale = bpy.data.objects[dropbox].scale

        for i, obj in enumerate(self.objs):
            if obj['bpy'] is None:
                continue

            obj['bpy'].location.x = drop_location.x + (rnd[i, 0] - .5) * 2.0 * drop_scale[0]
            obj['bpy'].location.y = drop_location.y + (rnd[i, 1] - .5) * 2.0 * drop_scale[1]
            obj['bpy'].location.z = drop_location.z + (rnd[i, 2] - .5) * 2.0 * drop_scale[2]
            obj['bpy'].rotation_euler = Vector((rnd_rot[i, :] * np.pi))

            self.logger.info(f"Object {obj['object_class_name']}: {obj['bpy'].location}, {obj['bpy'].rotation_euler}")

        # update the scene. unfortunately it doesn't always work to just set
        # the location of the object without recomputing the dependency
        # graph
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

    def randomize_environment_texture(self):
        # set some environment texture, randomize, and render
        env_txt_filepath = expandpath(random.choice(self.environment_textures))
        self.renderman.set_environment_texture(env_txt_filepath)

    def forward_simulate(self):
        self.logger.info(f"forward simulation of {self.config.scene_setup.forward_frames} frames")
        scene = bpy.context.scene
        for i in range(self.config.scene_setup.forward_frames):
            scene.frame_set(i + 1)

    def activate_camera(self, cam: str):
        # first get the camera name. this depends on the scene (blend file)
        # and is of the format CameraName.XXX, where XXX is a number with
        # leading zeros
        cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
        bpy.context.scene.camera = bpy.context.scene.objects[cam_name]

    def test_visibility(self):
        for i_cam, cam in enumerate(self.config.scene_setup.cameras):
            cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
            cam_obj = bpy.data.objects[cam_name]
            self.any_visible_object = False
            self.all_objects_visible = True
            for obj in self.objs:
                not_visible_or_occluded = abr_geom.test_occlusion(
                    bpy.context.scene,
                    bpy.context.scene.view_layers['View Layer'],
                    cam_obj,
                    obj['bpy'],
                    bpy.context.scene.render.resolution_x,
                    bpy.context.scene.render.resolution_y,
                    require_all=False,
                    origin_offset=0.01)
                if not_visible_or_occluded:
                    self.all_objects_visible = False
                else:
                    self.any_visible_object = True
            if not_visible_or_occluded:
                self.logger.warn(f"object {obj} not visible or occluded")
                if self.config.logging.debug:
                    self.logger.info(f"saving blender file for debugging to /tmp/workstationscenarios.blend")
                    bpy.ops.wm.save_as_mainfile(filepath="/tmp/workstationscenarios.blend")
                return False
        return True

    def generate_dataset(self):
        """This will generate the dataset according to the configuration that
        was passed in the constructor.
        """

        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        format_width = int(ceil(log(image_count, 10)))

        i = 0
        while i < self.config.dataset.image_count:
            self.logger.info(f"Generating image {i + 1} of {self.config.dataset.image_count}")

            # generate render filename
            base_filename = "{:0{width}d}".format(i, width=format_width)

            # randomize scene: move objects at random locations, and forward
            # simulate physics
            self.randomize_environment_texture()
            self.randomize_object_transforms()
            self.forward_simulate()

            # repeat if the cameras cannot see the objects
            repeat_frame = False
            if not self.test_visibility():
                self.logger.warn("\033[1;33mObject(s) not visible from every camera. Re-randomizing... \033[0;37m")
                repeat_frame = True
            else:
                # loop through all cameras
                for i_cam, cam in enumerate(self.config.scene_setup.cameras):
                    # activate camera
                    self.activate_camera(cam)
                    # update path information in compositor
                    self.renderman.setup_pathspec(self.dirinfos[i_cam], base_filename, self.objs)
                    # finally, render
                    self.renderman.render()

                    # postprocess. this will take care of creating additional
                    # information, as well as fix filenames
                    try:
                        self.renderman.postprocess(self.dirinfos[i_cam], base_filename,
                                                   bpy.context.scene.camera, self.objs,
                                                   self.config.camera_info.zeroing)
                    except ValueError:
                        # This issue happens every now and then. The reason might be (not
                        # yet verified) that the target-object is occluded. In turn, this
                        # leads to a zero size 2D bounding box...
                        self.logger.error(
                            f"\033[1;31mValueError during post-processing, re-generating image index {i}\033[0;37m")
                        repeat_frame = True

                        # no need to continue with other cameras
                        break

            # if we need to repeat this frame, then do not increment the counter
            if not repeat_frame:
                i = i + 1

        return True

    def generate_viewsphere_dataset(self):
        # TODO: This dataset does not yet suppor viewsphere data generation
        """This will generate the dataset according to the configuration that
               was passed in the constructor.
               """
        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        # format_width = int(ceil(log(image_count, 10)))

        i_frm = 0
        while i_frm < int(self.config.scene_setup.num_frames):
            self.logger.info(f"Generating image {i_frm + 1} of {self.config.dataset.image_count}")

            # randomize scene: move objects at random locations, and forward
            # simulate physics
            self.randomize_environment_texture()
            self.randomize_object_transforms()
            self.forward_simulate()

            # set camera locations
            self.config.scene_setup.num_camera_locations = int(self.config.scene_setup.num_camera_locations)
            if self.config.scene_setup.num_camera_locations > 1:
                locations_list = camera_utils.generate_locations_list(
                    num_locations=self.config.scene_setup.num_camera_locations)

            # repeat if the cameras cannot see the objects
            self.test_visibility()
            repeat_frame = False
            if self.any_visible_object == False:
                print('\n\n\n ~~~~~~~~~~~~~~~~~~~~~~~~~` \n ~~~~~~~~~~~~~~~~~~~~~~~~ \n NO OBJECT VISIBLE! \n ~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n ~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n\n\n')
            if False:
                zzzzz = 8
            # if not self.any_visible_object:
            #     self.logger.warn(f"\033[1;33mObject(s) not visible from every camera. Re-randomizing... \033[0;37m")
                # repeat_frame = True
            # if not self.test_visibility():
            #     self.logger.warn(f"\033[1;33mObject(s) not visible from every camera. Re-randomizing... \033[0;37m")
            #     repeat_frame = True
            else:
                # use the first camera and move it across all views
                i_cam = 0
                cam = self.config.scene_setup.cameras[i_cam]
                # activate camera
                self.activate_camera(cam)
                for i_loc, loc in enumerate(locations_list):
                    # generate render filename
                    base_filename = f"scenario_{i_frm:04}_cameralocation_{i_loc:04}"
                    # update camera location
                    self.set_camera_location(location=loc)
                    # update path information in compositor
                    self.renderman.setup_pathspec(self.dirinfos[i_cam], base_filename, self.objs)
                    # finally, render
                    self.renderman.render()

                    # postprocess. this will take care of creating additional
                    # information, as well as fix filenames
                    # try:
                    self.renderman.postprocess(self.dirinfos[i_cam], base_filename,
                                                   bpy.context.scene.camera, self.objs,
                                                   self.config.camera_info.zeroing)
                    # except ValueError:
                    #     # This issue happens every now and then. The reason might be (not
                    #     # yet verified) that the target-object is occluded. In turn, this
                    #     # leads to a zero size 2D bounding box...
                    #     self.logger.error(
                    #         f"\033[1;31mValueError during post-processing, re-generating image index {i_frm}\033[0;37m")
                    #     repeat_frame = True
                    #     print(
                    #
                    #     # no need to continue with other cameras
                    #     break

            # if we need to repeat this frame, then do not increment the counter
            if not repeat_frame:
                i_frm = i_frm + 1
        return True

    def set_camera_location(self, location=(0, 0, 2)):
        # scene = bpy.context.scene
        for cam in self.config.scene_setup.cameras:
            # first get the camera name. this depends on the scene (blend file)
            # and is of the format CameraName.XXX, where XXX is a number with
            # leading zeros
            cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
            # select the camera. Blender often operates on the active object, to
            # make sure that this happens here, we select it
            blnd.select_object(cam_name)
            # set camera location
            bpy.data.objects[cam_name].location = location

    def dump_config(self):
        """Dump configuration to a file in the output folder(s)."""
        # dump config to each of the dir-info base locations, i.e. for each
        # camera that was rendered we store the configuration
        for dirinfo in self.dirinfos:
            output_path = dirinfo.base_path
            pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
            dump_config(self.config, output_path)

    def teardown(self):
        """Tear down the scene"""
        # nothing to do
        pass
