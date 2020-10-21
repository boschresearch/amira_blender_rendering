##!/usr/bin/env python

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

"""
This file implements generation of datasets for the Panda Table scenario. The
file depends on a suitable panda table blender file such as
robottable_empty.blend in $AMIRA_DATA_GFX.
"""

import bpy
import os
import pathlib
from mathutils import Vector
import numpy as np
import random
from math import ceil, log

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.interfaces as interfaces
from amira_blender_rendering.datastructures import Configuration
from amira_blender_rendering.utils.annotation import ObjectBookkeeper


_scene_name = 'PandaTable'

@abr_scenes.register(name=_scene_name, type='config')
class PandaTableConfiguration(abr_scenes.BaseConfiguration):
    """This class specifies all configuration options for the Panda Table scenario."""

    def __init__(self):
        super(PandaTableConfiguration, self).__init__()

        # specific scene configuration
        self.add_param('scene_setup.blend_file', '~/gfx/modeling/robottable_empty.blend',
                       'Path to .blend file with modeled scene')
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images',
                       'Path to background images / environment textures')
        self.add_param('scene_setup.cameras',
                       ['Camera,' 'StereoCamera.Left', 'StereoCamera.Right', 'Camera.FrontoParallel.Left',
                        'Camera.FrontoParallel.Right'], 'Cameras to render')
        self.add_param('scene_setup.forward_frames', 25, 'Number of frames in physics forward-simulation')

        # scenario: target objects
        self.add_param('scenario_setup.target_objects', [], 'List of objects to drop in the scene for which annotated info are stored')
        self.add_param('scenario_setup.distractor_objects', [], 'List of objects to drop in the scene for which info are NOT stored'
                       'List of objects visible in the scene but of which infos are not stored')
        
        # multiview configuration (if implemented)
        self.add_param('multiview_setup.mode', '',
                       'Selected mode to generate view points, i.e., random, bezier, viewsphere')
        self.add_param('multiview_setup.mode_config', Configuration(), 'Mode specific configuration')

        self.add_param('logging.plot', False, 'If True, in debug mode, enable simple visual debug')
        self.add_param('logging.plot_axis', False, 'If True, in debug-plot mode, plot camera coordinate systems')
        self.add_param('logging.scatter', False, 'If True, in debug mode-plot, enable scatter plot')
        self.add_param('logging.save_to_blend', False, 'If True, in debug mode, log to .blend files')


@abr_scenes.register(name=_scene_name, type='scene')
class PandaTable(interfaces.ABRScene):

    def __init__(self, **kwargs):
        super(PandaTable, self).__init__()
        self.logger = get_logger()

        # we do composition here, not inheritance anymore because it is too
        # limiting in its capabilities. Using a render manager is a better way
        # to handle compositor nodes
        self.renderman = abr_scenes.RenderManager()

        # extract configuration, then build and activate a split config
        self.config = kwargs.get('config', PandaTableConfiguration())
        # this check that the given configuration is (or inherits from) of the correct type
        if not isinstance(self.config, PandaTableConfiguration):
            raise RuntimeError(f"Invalid configuration of type {type(self.config)} for class PandaTable")
        
        # determine if we are rendering in multiview mode
        self.render_mode = kwargs.get('render_mode', 'default')
        if self.render_mode not in ['default', 'multiview']:
            self.logger.warn(f'render mode "{self.render_mode}" not supported. Falling back to "default"')
            self.render_mode = 'default'
        
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

        # populate the scene with objects (target and non)
        self.objs = self.setup_objects(self.config.scenario_setup.target_objects, bpy_collection='TargetObjects')
        self.distractors = self.setup_objects(self.config.scenario_setup.distractor_objects,
                                              bpy_collection='DistractorObjects')

        # finally, setup the compositor
        self.setup_compositor()

    def postprocess_config(self):

        # depending on the rendering mode (standard or multiview), determine number of images
        if self.render_mode == 'default':
            # in default mode (i.e., single view), image_count control the number of images (hence scene) to render
            self.config.dataset.view_count = 1
            self.config.dataset.scene_count = self.config.dataset.image_count
        elif self.render_mode == 'multiview':
            # in multiview mode: image_count = scene_count * view_count
            self.config.dataset.scene_count = max(1, self.config.dataset.scene_count)
            self.config.dataset.view_count = max(1, self.config.dataset.view_count)
            self.config.dataset.image_count = self.config.dataset.scene_count * self.config.dataset.view_count
        else:
            self.logger.error(f'render mode {self.render_mode} currently not supported')
            raise ValueError(f'render mode {self.render_mode} currently not supported')

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

    def setup_dirinfo(self):
        """Setup directory information for all cameras.

        This will be required to setup all path information in compositor nodes
        """
        # compute directory information for each of the cameras
        self.dirinfos = list()
        for cam in self.config.scene_setup.cameras:
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
        cam_name = self.get_camera_name(cam_str)
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
            # first get the camera name. This depends on the scene (blend file)
            cam_name = self.get_camera_name(cam)
            # select the camera. Blender often operates on the active object, to
            # make sure that this happens here, we select it
            blnd.select_object(cam_name)
            # modify camera according to the intrinsics
            blender_camera = bpy.data.objects[cam_name].data
            # set the calibration matrix
            camera_utils.set_camera_info(scene, blender_camera, self.config.camera_info)

    def setup_objects(self, objects: list, bpy_collection: str = 'TargetObjects'):
        """This method populates the scene with objects.

        Object types and number of objects will be taken from the configuration.
        The format to specify objects is
            ObjectType:Number
        where ObjectType should be the name of an object that exists in the
        blender file, and number indicates how often the object shall be
        duplicated.
        
        Args:
            objects(list): list of ObjectType:Number to setup
            bpy_collection(str): Name of bpy collection the given objects are
                linked to in the .blend file. Default: TargetObjects
                If the given objects are non-target (i.e., they populate the scene but
                no information regarding them are stored) use a different collection.

        Returns:
            objs(list): list of dict to handle desired objects
        """
        # let's start with an empty list
        objs = []
        obk = ObjectBookkeeper()

        # first reset the render pass index for all panda model objects (links,
        # hand, etc)
        links = [f'Link-{i}' for i in range(8)] + ['Finger-Left', 'Finger-Right', 'Hand']
        for link in links:
            bpy.data.objects[link].pass_index = 0

        # extract all objects from the configuration. An object has a certain
        # type, as well as an own id. this information is storeed in the objs
        # list, which contains a dict. The dict contains the following keys:
        #       id_mask             used for mask computation, computed below
        #       object_class_name   type-name of the object
        #       object_class_id     model type ID (simply incremental numbers)
        #       object_id   instance ID of the object
        #       bpy         blender object reference
        for class_id, obj_spec in enumerate(objects):
            class_name, obj_count = obj_spec.split(':')

            # here we distinguish if we copy a part from the proto objects
            # within a scene, or if we have to load it from file
            is_proto_object = not class_name.startswith('parts.')
            if not is_proto_object:
                # split off the prefix for all files that we load from blender
                class_name = class_name[6:]

            # TODO: file loading happens only very late in this loop. This might
            #       be an issue for large object counts and could be changed to
            #       load-once copy-often.
            for j in range(int(obj_count)):
                # First, deselect everything
                bpy.ops.object.select_all(action='DESELECT')
                if is_proto_object:
                    # duplicate proto-object
                    blnd.select_object(class_name)
                    bpy.ops.object.duplicate()
                    new_obj = bpy.context.object
                else:
                    # we need to load this object from file. This could be
                    # either a blender file, or a PLY file
                    blendfile = expandpath(self.config.parts[class_name], check_file=False)
                    if os.path.exists(blendfile):
                        # this is a blender file, so we should load it
                        # we can now load the object into blender
                        # try-except logic to handle objects from same blend file but different
                        # class names to allow loading same objects with e.g., different scales
                        try:
                            bpy_obj_name = self.config.parts['name'][class_name]
                        except KeyError:
                            bpy_obj_name = class_name
                        blnd.append_object(blendfile, bpy_obj_name)
                        # NOTE: bpy.context.object is **not** the object that we are
                        # interested in here! We need to select it via original name
                        # first, then we rename it to be able to select additional
                        # objects later on
                        new_obj = bpy.data.objects[bpy_obj_name]
                        new_obj.name = f'{class_name}.{j:03d}'
                        # try to rescale object according to its blend_scale if given in the config
                        try:
                            new_obj.scale = Vector(self.config.parts.blend_scale[class_name])
                            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)
                        except KeyError:
                            # log and keep going
                            self.logger.info(f'No blend_scale for obj {class_name} given. Skipping!')
                    else:
                        # no blender file given, so we will load the PLY file
                        # NOTE: no try-except logic for ply since we are not binded to object names as for .blend
                        ply_path = expandpath(self.config.parts.ply[class_name], check_file=True)
                        bpy.ops.import_mesh.ply(filepath=ply_path)
                        # here we can use bpy.context.object!
                        new_obj = bpy.context.object
                        new_obj.name = f'{class_name}.{j:03d}'
                        # try to rescale object according to its ply_scale if given in the config
                        try:
                            new_obj.scale = Vector(self.config.parts.ply_scale[class_name])
                            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)
                        except KeyError:
                            # log and keep going
                            self.logger.info(f'No ply_scale for obj {class_name} given. Skipping!')
                
                # move object to collection: in case of debugging
                try:
                    collection = bpy.data.collections[bpy_collection]
                except KeyError:
                    collection = bpy.data.collections.new(bpy_collection)
                    bpy.context.scene.collection.children.link(collection)

                if new_obj.name not in collection.objects:
                    collection.objects.link(new_obj)

                # bookkeep instance
                obk.add(class_name)

                # append all information
                objs.append({
                    'id_mask': '',
                    'object_class_name': class_name,
                    'object_class_id': class_id,
                    'object_id': j,
                    'bpy': new_obj,
                    'visible': None
                })

        # build masks id for compositor of the format _N_M, where N is the model
        # id, and M is the object id
        w_class = ceil(log(len(obk), 10)) if len(obk) else 0  # format width for number of model types
        for i, obj in enumerate(objs):
            w_obj = ceil(log(obk[obj['object_class_name']]['instances'], 10))  # format width for objs with same model
            id_mask = f"_{obj['object_class_id']:0{w_class}}_{obj['object_id']:0{w_obj}}"
            obj['id_mask'] = id_mask
        
        return objs

    def setup_compositor(self):
        self.renderman.setup_compositor(self.objs, color_depth=self.config.render_setup.color_depth)

    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)

    def randomize_object_transforms(self, objs: list):
        """move all objects to random locations within their scenario dropzone,
        and rotate them.
        
        Args:
            objs(list): list of objects whose pose is randomized.
        
        NOTE: the list of objects must be mutable since the method does not return but directly modify them!
        """

        # we need #objects * (3 + 3)  many random numbers, so let's just grab them all
        # at once
        rnd = np.random.uniform(size=(len(objs), 3))
        rnd_rot = np.random.rand(len(objs), 3)

        # now, move each object to a random location (uniformly distributed) in
        # the scenario-dropzone. The location of a drop box is its centroid (as
        # long as this was not modified within blender). The scale is the scale
        # along the axis in one direction, i.e. the full extend along this
        # direction is 2 * scale.
        dropbox = f"Dropbox.000"
        drop_location = bpy.data.objects[dropbox].location
        drop_scale = bpy.data.objects[dropbox].scale

        for i, obj in enumerate(objs):
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
        self.logger.info(f'forward simulation: done!')

    def activate_camera(self, cam_name: str):
        # first get the camera name. this depends on the scene (blend file)
        bpy.context.scene.camera = bpy.context.scene.objects[f"{cam_name}"]

    def set_camera_location(self, name, location):
        """
        Set locations for selected cameras

        Args:
            name(str): camera name
            location(array-like): camera location
        """
        # select camera
        blnd.select_object(name)
        # set pose
        bpy.data.objects[name].location = location

    def get_camera_name(self, cam_str):
        """Get bpy camera name from camera string in config. This depends on the loaded blend file"""
        return f"{cam_str}"

    def test_visibility(self, camera_name: str, locations: np.array):
        """Test whether given camera sees all target objects
        and store visibility level/label for each target object
        
        Args:
            camera(str): selected camera name
            locations(list): list of locations to check. If None, check current camera location
        """

        # grep camera object from name
        camera = bpy.context.scene.objects[camera_name]

        # make sure to work with multi-dim array
        if locations.shape == (3,):
            locations = np.reshape(locations, (1, 3))
        
        # loop over locations
        for i_loc, location in enumerate(locations):
            camera.location = location

            any_not_visible_or_occluded = False
            for obj in self.objs:
                not_visible_or_occluded = abr_geom.test_occlusion(
                    bpy.context.scene,
                    bpy.context.scene.view_layers['View Layer'],
                    camera,
                    obj['bpy'],
                    bpy.context.scene.render.resolution_x,
                    bpy.context.scene.render.resolution_y,
                    require_all=False,
                    origin_offset=0.01)
                # store object visibility info
                obj['visible'] = not not_visible_or_occluded
                if not_visible_or_occluded:
                    self.logger.warn(f"object {obj} not visible or occluded")
            
                # keep trace if any obj was not visible or occluded
                any_not_visible_or_occluded = any_not_visible_or_occluded or not_visible_or_occluded

            # if any_not_visibile_or_occluded --> at least one object is not visible from one location: return False
            if any_not_visible_or_occluded:
                return False

        # --> all objects are visible (from all locations): return True
        return True

    def generate_dataset(self):
        """This will generate a multiview dataset according to the configuration that
        was passed in the constructor.
        """
        # The number of images in the dataset is controlled differently in case of default (singleview) vs multiview
        # rendering mode.
        # In default mode
        #   dataset.image_count controls the number of images
        #
        # In multiview mode
        #   dataset.image_count = dataset.scene_count * dataset.view_count
        #
        # In addition the [multiview] config section defines specific configuration such as
        #
        #   [multiview_setup]
        #   mode(str): how to generate camera locations for multiview. E.g., viewsphere, bezier, random
        #   mode_cfg(dict-like/config): additional mode specific configs

        # filename setup
        if self.config.dataset.image_count <= 0:
            return False
        scn_format_width = int(ceil(log(self.config.dataset.scene_count, 10)))
        
        camera_names = [self.get_camera_name(cam_str) for cam_str in self.config.scene_setup.cameras]
        if self.render_mode == 'default':
            cameras_locations = camera_utils.get_current_cameras_locations(camera_names)
            for cam_name, cam_location in cameras_locations.items():
                cameras_locations[cam_name] = np.reshape(cam_location, (1, 3))
        
        elif self.render_mode == 'multiview':
            cameras_locations, _ = camera_utils.generate_multiview_cameras_locations(
                num_locations=self.config.dataset.view_count,
                mode=self.config.multiview_setup.mode,
                camera_names=camera_names,
                config=self.config.multiview_setup.mode_config)
        
        else:
            raise ValueError(f'Selected render mode {self.render_mode} not currently supported')
       
        # some debug/logging options
        if self.config.logging.debug:
            # simple plot of generated camera locations
            if self.config.logging.plot:
                from amira_blender_rendering.math.curves import plot_points

                for cam_name in camera_names:
                    plot_points(np.array(cameras_locations[cam_name]),
                                bpy.context.scene.objects[cam_name],
                                plot_axis=self.config.logging.plot_axis,
                                scatter=self.config.logging.scatter)

            # save all generated camera locations to .blend for later debug
            if self.config.logging.save_to_blend:
                for i_cam, cam_name in enumerate(camera_names):
                    self.logger.info('For debugging purposes, saving all cameras locations to .blend')
                    self._save_to_blend(i_cam, camera_locations=cameras_locations[cam_name])

        # control loop for the number of static scenes to render
        scn_counter = 0
        while scn_counter < self.config.dataset.scene_count:

            # randomize scene: move objects at random locations, and forward simulate physics
            self.randomize_environment_texture()
            self.randomize_object_transforms(self.objs + self.distractors)
            self.forward_simulate()
            
            # check visibility
            repeat_frame = False
            if not self.config.render_setup.allow_occlusions:
                for cam_name, cam_locations in cameras_locations.items():
                    repeat_frame = not self.test_visibility(cam_name, cam_locations)

            # if we need to repeat (change static scene) we skip one iteration
            # without increasing the counter
            if repeat_frame:
                self.logger.warn(f'Something wrong. '
                                 f'Re-randomizing scene {scn_counter + 1}/{self.config.dataset.scene_count}')
                continue

            # loop over cameras
            for i_cam, cam_str in enumerate(self.config.scene_setup.cameras):
                # get bpy object camera name
                cam_name = self.get_camera_name(cam_str)

                # check whether we broke the for-loop responsible for image generation for
                # multiple camera views and repeat the frame by re-generating the static scene
                if repeat_frame:
                    break
                
                # extract camera locations
                cam_locations = cameras_locations[cam_name]
                
                # compute format width
                view_format_width = int(ceil(log(len(cam_locations), 10)))
                
                # activate camera
                self.activate_camera(cam_name)

                # loop over locations
                for view_counter, cam_loc in enumerate(cam_locations):

                    self.logger.info(f"Generating image for camera {cam_str}: "
                                     f"scene {scn_counter + 1}/{self.config.dataset.scene_count}, "
                                     f"view {view_counter + 1}/{self.config.dataset.view_count}")

                    # filename
                    base_filename = f"s{scn_counter:0{scn_format_width}}_v{view_counter:0{view_format_width}}"

                    # set camera location
                    self.set_camera_location(cam_name, cam_loc)

                    # at this point all the locations have already been tested for visibility
                    # according to allow_occlusions config.
                    # Here, we re-run visibility to set object visibility level as well as to update
                    # the depsgraph needed to update translation and rotation info
                    all_visible = self.test_visibility(cam_name, cam_loc)

                    if not all_visible:
                        if self.config.logging.debug and self.config.logging.save_to_blend:
                            self.logger.info('One or more objects are not visible. Saving debug data to .blend')
                            self._save_to_blend(i_cam, scene_index=scn_counter, view_index=view_counter)

                    # update path information in compositor
                    self.renderman.setup_pathspec(self.dirinfos[i_cam], base_filename, self.objs)
                    
                    # finally, render
                    self.renderman.render()

                    # postprocess. this will take care of creating additional
                    # information, as well as fix filenames
                    try:
                        self.renderman.postprocess(
                            self.dirinfos[i_cam],
                            base_filename,
                            bpy.context.scene.camera,
                            self.objs,
                            self.config.camera_info.zeroing,
                            rectify_depth=self.config.postprocess.rectify_depth,
                            overwrite=self.config.postprocess.overwrite,
                            visibility_from_mask=self.config.postprocess.visibility_from_mask)

                    except ValueError:
                        self.logger.error(
                            f"\033[1;31mValueError during post-processing. "
                            f"Re-generating image {scn_counter + 1}/{self.config.dataset.scene_count}\033[0;37m")
                        repeat_frame = True

                        # if requested save to blend files for debugging
                        if self.config.logging.debug and self.config.logging.save_to_blend:
                            self.logger.error('There might be a discrepancy between generated mask and '
                                              'object visibility data. Saving debug info to .blend')
                            self._save_to_blend(i_cam, scene_index=scn_counter, view_index=view_counter, on_error=True)

                        break

            # update scene counter
            if not repeat_frame:
                scn_counter = scn_counter + 1

        return True

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

    def _save_to_blend(self, camera_index: int, **kw):
        # TODO: move to basescenemanager?
        """
        Save log data to .blend files

        The behavior of the method depends on its keywords input arguments. 
        In particular:
            - with no optional args: it logs the current active scene to .blend in ActiveCamera/Logs
                                    where CurrentCamera identify the directory where data, i.e.,
                                    Images and Annotations, for the active camera are dumped
            - with camera_locations: the active camera is duplicated and move in all given locations.
                                    Use this behavior to check whether generated locations are valid.
            - with view_index and scene_index: the current active scene is logged to .blend with
                                                following our base filenaming convention
                - if additionally on_error == True: data are logged to a separate timestamped subdirectory
                                                    (together with additional data) to avoid data overwrite

        Args:
            camera_index(int): active camera index as in self.config.scene_setup.cameras
        
        Kwargs Args:
            camera_locations(list): list containing multiple camera locations
            scene_index(int): index of static scene being rendered
            view_index(int): index of current view being rendered
            on_error(bool): if True, assume an error has been raised and additional data are logged
        """
        # extract and check args
        camera_locations = kw.get('camera_locations', None)
        scn_idx = kw.get('scene_index', None)
        view_idx = kw.get('view_index', None)
        on_error = kw.get('on_error', False)

        if camera_locations is not None and (scn_idx is not None or view_idx is not None or on_error):
            raise ValueError('Given arguments are mutually exclusive')

        # extract and create (if necessary) log directory (for each camera)
        logpath = os.path.join(self.dirinfos[camera_index].base_path, 'Logs')
        if on_error:
            from datetime import datetime
            from shutil import copyfile
            now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            logpath = os.path.join(logpath, now)
        pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)

        # file specs
        scn_frmt_w = int(ceil(log(self.config.dataset.scene_count, 10)))
        view_frmt_w = int(ceil(log(self.config.dataset.view_count, 10)))
        scn_str = '' if scn_idx is None else f'_s{scn_idx:0{scn_frmt_w}}'
        view_str = '' if view_idx is None else f'_v{view_idx:0{view_frmt_w}}'

        filename = f'robottable' + scn_str + view_str + f'.blend'
        filepath = os.path.join(logpath, filename)
   
        # create and link temporary collection
        if camera_locations is not None:
            cam_name = self.get_camera_name(self.config.scene_setup.cameras[camera_index])
            tmp_cam_coll = bpy.data.collections.new('TemporaryCameras')
            bpy.context.scene.collection.children.link(tmp_cam_coll)

            tmp_cameras = []
            for location in camera_locations:
                blnd.select_object(cam_name)
                bpy.ops.object.duplicate()
                # TODO: remove from original collection to avoid name clutter in .blend
                tmp_cam_obj = bpy.context.object
                tmp_cam_obj.location = location
                tmp_cam_coll.objects.link(tmp_cam_obj)
                tmp_cameras.append(tmp_cam_obj)
            bpy.context.evaluated_depsgraph_get().update()
   
        self.logger.info(f"Saving blender file for debugging to {filepath}")
        bpy.ops.wm.save_as_mainfile(filepath=filepath)

        # clear objects and collection
        if camera_locations is not None:
            bpy.ops.object.select_all(action='DESELECT')
            for tmp_cam in tmp_cameras:
                bpy.data.objects.remove(tmp_cam)
            bpy.data.collections.remove(tmp_cam_coll)
            
        # on error we save additional files
        if on_error:
            self.logger.error('Saving to .blend on error. Logging additional data')
            # copy rgb
            rgbname = scn_str[1:] + view_str + f'.png'
            srcpath = os.path.join(self.dirinfos[camera_index].images.const, rgbname)
            dstpath = os.path.join(logpath, rgbname)
            copyfile(srcpath, dstpath)
            # copy masks
            for obj in self.objs:
                maskname = scn_str[1:] + view_str + f'{obj["id_mask"]}.png'
                srcpath = os.path.join(self.dirinfos[camera_index].images.mask, maskname)
                dstpath = os.path.join(logpath, maskname)
                copyfile(srcpath, dstpath)
