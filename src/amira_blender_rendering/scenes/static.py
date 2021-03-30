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
This file implements generation of datasets from "static" scenes. That is scene where
no dynamic simulation is performed.

Differently from dynamical scenes, this foresees all the desired objects already loaded
in the scene. For this to work, the selected target objects in the config must match
those in the loaded blender file. These are not actively used for simulation
but to correctly write data to file.
"""

import bpy
import pathlib
import numpy as np
import random
from math import ceil, log

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.utils.blender as blnd
from amira_blender_rendering.utils.annotation import ObjectBookkeeper


# scene name for registration
_scene_name = 'StaticScene'


@abr_scenes.register(name=_scene_name, type='config')
class StaticSceneConfiguration(abr_scenes.BaseConfiguration):
    """This class specifies all configuration options for the Panda Table scenario."""

    def __init__(self):
        super(StaticSceneConfiguration, self).__init__()

        # specific scene configuration
        self.add_param('scene_setup.blend_file', '~/gfx/modeling/robottable_empty.blend',
                       'Path to .blend file with modeled scene')
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images',
                       'Path to background images / environment textures')
        self.add_param('scene_setup.camera_groups', [], 'List if camera groups to render, each with its own configs')

        # scenario: target objects
        self.add_param('scenario_setup.target_objects', [],
                       'List of objects to drop in the scene for which annotated info are stored')
        self.add_param('scenario_setup.textured_objects', [],
                       'List of objects whose texture is randomized during rendering')
        self.add_param('scenario_setup.objects_textures', '', 'Path to images for object textures')

        # multiview configuration (if implemented)
        self.add_param('multiview_setup.mode', '',
                       'Selected mode to generate view points, i.e., random, bezier, viewsphere')

        # specific debug config
        self.add_param('debug.plot', False, 'If True, in debug mode, enable simple visual debug')
        self.add_param('debug.plot_axis', False, 'If True, in debug-plot mode, plot camera coordinate systems')
        self.add_param('debug.scatter', False, 'If True, in debug mode-plot, enable scatter plot')
        self.add_param('debug.save_to_blend', False, 'If True, in debug mode, log to .blend files')


@abr_scenes.register(name=_scene_name, type='scene')
class StaticScene(abr_scenes.BaseABRScene):

    def __init__(self, **kwargs):
        super(StaticScene, self).__init__()

        # extract configuration, then build and activate a split config
        self.config = kwargs.get('config', StaticSceneConfiguration())
        # this check that the given configuration is (or inherits from) of the correct type
        if not isinstance(self.config, StaticSceneConfiguration):
            raise RuntimeError(f"Invalid configuration of type {type(self.config)} for class {_scene_name}")
        
        # determine if we are rendering in multiview mode
        self.render_mode = kwargs.get('render_mode', 'default')
        self.check_supported_render_modes(self.render_mode, ['default', 'multiview'])
        
        # we might have to post-process the configuration
        self.postprocess_config()

        # handle multiple camera groups
        self.load_camera_group_configs()

        # setup directory information for each camera in each grop
        for cam_grp in self.config.scene_setup.camera_groups:
            for cam_name in self.config[cam_grp].names:
                self.setup_dirinfo(cam_name)

        # setup the scene, i.e. load it from file
        self.setup_scene()

        # setup the renderer. do this _AFTER_ the file was loaded during
        # setup_scene(), because otherwise the information will be taken from
        # the file, and changes made by setup_renderer ignored
        self.setup_renderer()

        # grab environment textures
        self.setup_environment_textures()

        # setup objects for which the user want to randomize the texture
        self.setup_textured_objects()

        # setup all camera information according to the configuration
        self.setup_cameras()

        # setup global render output configuration
        self.setup_render_output()

        # populate the scene with objects (target and non)
        self.objs = self.setup_objects(self.config.scenario_setup.target_objects)

        # finally, setup the compositor
        self.setup_compositor(self.objs, color_depth=self.config.render_setup.color_depth)

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
    
    def setup_cameras(self):
        """Setup all cameras in all selected camera groups.
        Each camera group has the same config.
        """
        for grp_name in self.config.scene_setup.camera_groups:
            # get config for the group
            grp_config = self.config[grp_name]
            # loop over each camera in the group
            for cam_name in grp_config.names:
                # use default method from parent to setup camera
                self.setup_camera(cam_name,
                                  grp_config,
                                  width=self.config.render_setup.width,
                                  height=self.config.render_setup.height)

    def setup_render_output(self):
        """setup render output dimensions. This is not set for a specific camera,
        but in renders render environment.

        Note that this should be called _after_ cameras were set up, because
        their setup might influence these values.
        """

        # first set the resolution if it was specified in the configuration
        if (self.config.render_setup.width > 0) and (self.config.render_setup.height > 0):
            bpy.context.scene.render.resolution_x = self.config.render_setup.width
            bpy.context.scene.render.resolution_y = self.config.render_setup.height

        # Setting the resolution can have an impact on the calibration matrix
        # that was used for rendering. Hence, we will store the effective
        # calibration matrix K alongside. Because we use identical cameras, we
        # can extract this from one of the cameras
        self.get_effective_intrinsics()
    
    def get_effective_intrinsics(self):
        """Get the effective intrinsics (for each camera grop) that were used during rendering.

        This function will copy original values for intrinsic, sensor_width, and
        focal_length, and fov, to the configuration an prepend them with 'original_'. This
        way, they are available in the dataset later on
        """
        for cam_group in self.config.scene_setup.camera_groups:
            # get group configs
            grp_config = self.config[cam_group]
            # pick one camera from the group. They all have the same intrinsics
            cam_name = grp_config.names[0]
            cam = bpy.data.objects[cam_name].data
            # get the effective intrinsics
            effective_intrinsic = camera_utils.get_intrinsics(bpy.context.scene, cam)
            # store in configuration (and backup original values)
            if grp_config.intrinsic is not None:
                grp_config.original_intrinsic = grp_config.intrinsic
            else:
                grp_config.original_intrinsic = ''
            grp_config.intrinsic = list(effective_intrinsic)

    def setup_objects(self, objects: list):
        """This method retrieves objects info from the loaded bledner file.

        Being a static scene, it is assumed objects are already loaded in the blender file.

        Object types and number of objects will be taken from the configuration.
        The format to specify objects is
            ObjectType:Number
        where ObjectType should be the name of an object that exists in the
        blender file, and number indicates how often the object shall be
        duplicated.
        
        Args:
            objects(list): list of ObjectType:Number to setup

        Returns:
            objs(list): list of dict to handle desired objects
        """
        # let's start with an empty list
        objs = []
        obk = ObjectBookkeeper()

        # extract all objects from the configuration. An object has a certain
        # type, as well as an own id. this information is storeed in the objs
        # list, which contains a dict. The dict contains the following keys:
        #       id_mask             used for mask computation, computed below
        #       object_class_name   type-name of the object
        #       object_class_id     model type ID (simply incremental numbers)
        #       object_id   instance ID of the object
        #       bpy         blender object reference
        for class_id, obj_spec in enumerate(objects):
            if obj_spec is None or obj_spec == '':
                return

            class_name, obj_count = obj_spec.split(':')

            if class_name.startswith('parts.'):
                # split off the prefix for all files that we load from blender
                class_name = class_name[6:]

            # go over the object instances
            for j in range(int(obj_count)):
                # First, deselect everything
                bpy.ops.object.select_all(action='DESELECT')

                # retrieve object name. We assume object instances follow the standard convention
                # class_name.xxx where xxx is an increasing number starting at 000.
                bpy_obj_name = f'{class_name}.{j:03d}'
                blnd.select_object(bpy_obj_name)
                new_obj = bpy.context.object
                                    
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

    def setup_textured_objects(self):
        # get list of textures
        self.objects_textures = get_environment_textures(self.config.scenario_setup.objects_textures)
        # check whether given objects exists
        for name in self.config.scenario_setup.textured_objects:
            if bpy.data.objects.get(name) is None:
                self.logger.warn(f'Given object {name} not among available object in the scene. Popping!')
                self.config.scenario_setup.textured_objects.remove(name)

    def randomize_environment_texture(self):
        # TODO: finit world object (also in PandaTable)
        # set some environment texture, randomize, and render
        env_txt_filepath = expandpath(random.choice(self.environment_textures))
        self.renderman.set_environment_texture(env_txt_filepath)

    def randomize_textured_objects_textures(self):
        for obj_name in self.config.scenario_setup.textured_objects:
            obj_txt_filepath = expandpath(random.choice(self.objects_textures))
            self.renderman.set_object_texture(obj_name, obj_txt_filepath)

    def test_visibility(self, cam_name: str, cam_poses: list):
        """Test whether given camera sees target objects from a given (list of) pose(s)
        and store visibility level/label for each target object
        
        Args:
            cam_name(str): selected camera name
            cam_poses([Matrix]): list of poses to check.

        Returns:
            bool: True if all objects are visible from all viewpoints, False otherwise.
        
        NOTE: objects information are also updated
        """
        # grep camera object from name
        camera = bpy.context.scene.objects[cam_name]

        # if a single pose if given, convert to list
        cam_poses = [cam_poses] if not isinstance(cam_poses, list) else cam_poses
        
        # loop over locations
        for pose in cam_poses:
            camera.matrix_world = pose

            any_not_visible_or_occluded = False
            for obj in self.objs:
                # NOTE: the dependency graph is updates inside the test
                # to make sure the pose takes effect
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

        # --> all objects are visible (from all view points): return True
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
        
        # get names of all the cameras to render
        camera_names = []
        camera_groups = []
        for cam_grp in self.config.scene_setup.camera_groups:
            for cam_name in self.config[cam_grp].names:
                camera_groups.append(cam_grp)
                camera_names.append(cam_name)

        # generate poses according to render mode and configs
        cameras_poses = self.get_cameras_poses(camera_names)

        # some debug options
        # NOTE: at this point the object of interest have been loaded in the blender
        # file but their positions have not yet been randomized..so they should all be located
        # at the origin
        if self.config.debug.enabled:
            self._debug_plot(camera_names, cameras_poses)

        # TODO: below (this is different from pandatable)
        # control loop for the number of static scenes to render
        scn_counter = 0
        retry = 0
        MAX_RETRY = 5
        while scn_counter < self.config.dataset.scene_count:

            # randomize scene: move objects at random locations, and forward simulate physics
            self.randomize_environment_texture()
            self.randomize_textured_objects_textures()
            
            # check visibility
            repeat_frame = False
            if not self.config.render_setup.allow_occlusions:
                for cam_name, cam_poses in cameras_poses.items():
                    repeat_frame = not self.test_visibility(cam_name, cam_poses)

            # if we need to repeat (change static scene) we skip one iteration
            # without increasing the counter
            if repeat_frame:
                self.logger.error('Something wrong (possibly due to visibility configurations).'
                                  ' Make sure your static scene and config are correct. Exiting!')
                exit(-1)

            # loop over cameras
            for i_cam, (cam_name, cam_poses) in enumerate(cameras_poses.items()):

                # check whether we broke the for-loop responsible for image generation for
                # multiple camera views and repeat the frame by re-generating the static scene
                if repeat_frame:
                    # retry at most 'max_retry' times then exit
                    if retry < MAX_RETRY:
                        break
                    self.logger.error(f'Max num of {MAX_RETRY} retry reached. Check your static scene is correct. Exit')
                    exit(-1)

                # compute format width
                view_format_width = int(ceil(log(len(cam_poses), 10)))
                
                # activate camera
                self.activate_camera(cam_name)

                # loop over locations
                for view_counter, cam_pose in enumerate(cam_poses):

                    self.logger.info(f"Generating image for camera {cam_name}: "
                                     f"scene {scn_counter + 1}/{self.config.dataset.scene_count}, "
                                     f"view {view_counter + 1}/{self.config.dataset.view_count}")

                    # filename
                    base_filename = f"s{scn_counter:0{scn_format_width}}_v{view_counter:0{view_format_width}}"

                    # set camera location
                    self.set_camera_pose(cam_name, cam_pose)

                    # at this point all the locations have already been tested for visibility
                    # according to allow_occlusions config.
                    # Here, we re-run visibility to set object visibility level as well as to update
                    # the depsgraph needed to update translation and rotation info
                    all_visible = self.test_visibility(cam_name, cam_pose)

                    if not all_visible:
                        # if debug is enabled save to blender for debugging
                        if self.config.debug.enabled and self.config.debug.save_to_blend:
                            self.save_to_blend(
                                self.dirinfos[i_cam],
                                scene_index=scn_counter,
                                view_index=view_counter,
                                basefilename='robottable_visibility')

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
                            self.config[camera_groups[i_cam]].zeroing,
                            depth_scale=self.config.postprocess.depth_scale,
                            visibility_from_mask=self.config.postprocess.visibility_from_mask,
                            camera_config=self.config[camera_groups[i_cam]])
                        
                        if self.config.debug.enabled and self.config.debug.save_to_blend:
                            # reset frame to 0 and save
                            current_frame = bpy.context.scene.frame_current
                            bpy.context.scene.frame_set(0)
                            self.save_to_blend(
                                self.dirinfos[i_cam],
                                scene_index=scn_counter,
                                view_index=view_counter,
                                basefilename='robottable')
                            bpy.context.scene.frame_set(current_frame)

                    except ValueError:
                        self.logger.error(
                            f"\033[1;31mValueError during post-processing. "
                            f"Re-generating image {scn_counter + 1}/{self.config.dataset.scene_count}\033[0;37m")
                        repeat_frame = True
                        retry += 1

                        # if requested save to blend files for debugging
                        if self.config.debug.enabled and self.config.debug.save_to_blend:
                            self.logger.error('There might be a discrepancy between generated mask and '
                                              'object visibility data. Saving debug info to .blend')
                            self.save_to_blend(
                                self.dirinfos[i_cam],
                                scene_index=scn_counter,
                                view_index=view_counter,
                                on_error=True,
                                basefilename='robottable')

                        break

            # update scene counter
            if not repeat_frame:
                scn_counter = scn_counter + 1

        return True

    def _debug_plot(self, camera_names, cameras_poses):
        """Support method to plot during debug

        Args:
            camera_names(list(str)): list with names of blender camera objects
            cameras_poses(dict(list)): dictionary with list of 3d Matrix poses for each camera
        
        Returns: None

            The behavior depends on the debug flags set in the configuration.
             - if debug.plot is True:
                generate simple plot of multiple camera locations
            
             - if debug.plot.save_to_blend is True:
                save for each camera in a separate .blend file a copy of the camera
                in each given pose
        """
        from amira_blender_rendering.math.curves import plot_transforms
        # iterate over cameras
        for i_cam, cam_name in enumerate(camera_names):
            # simple plot of generated camera locations
            if self.config.debug.plot:
                plot_transforms(cameras_poses[cam_name],
                                plot_axis=self.config.debug.plot_axis,
                                scatter=self.config.debug.scatter)

            # save all generated camera locations to .blend for later debug
            if self.config.debug.save_to_blend:
                self.save_to_blend(
                    self.dirinfos[i_cam],
                    camera_name=cam_name,
                    camera_poses=cameras_poses[cam_name],
                    basefilename='robottable_camera_poses')

    def get_cameras_poses(self, camera_names):
        """Generate camera poses according to render mode and given configuration values

        Args:
            camera_names(list(str)): list of blender camera object names
        
        Returns:
            cameras_poses(dist(list)): dictionary with list of poses for each camera
        """
        # Default mode uses blender file setup.
        # We assume all necessary/desired constraints are already set.
        # We simply get the current poses
        if self.render_mode == 'default':
            cameras_poses = {}
            for cam_name in camera_names:
                cameras_poses[cam_name] = [camera_utils.get_camera_pose(cam_name)]
        
        # in multiview rendering, we generate first a list of locations for the given
        # center group and then, add constraints to track a desired aim and move the cameras
        # around compute relative poses depending on their group type
        elif self.render_mode == 'multiview':
            locations = camera_utils.generate_multiview_locations(
                num_locations=self.config.dataset.view_count,
                mode=self.config.multiview_setup.mode,
                config=self.config.multiview_setup[self.config.multiview_setup.mode])

            # compute poses
            cameras_poses = camera_utils.compute_cameras_poses(
                self.config.scene_setup.camera_groups, self.config, locations)

        else:
            raise ValueError(f'Selected render mode {self.render_mode} not currently supported')

        return cameras_poses