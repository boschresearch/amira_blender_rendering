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
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.interfaces as interfaces
from amira_blender_rendering.datastructures import Configuration
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
        self.add_param('scene_setup.cameras',
                       ['Camera', 'StereoCamera.Left', 'StereoCamera.Right', 'Camera.FrontoParallel.Left',
                        'Camera.FrontoParallel.Right'], 'Cameras to render')

        # scenario: target objects
        self.add_param('scenario_setup.target_objects', [],
                       'List of objects to drop in the scene for which annotated info are stored')
        self.add_param('scenario_setup.textured_objects', [],
                       'List of objects whose texture is randomized during rendering')
        self.add_param('scenario_setup.objects_textures', '', 'Path to images for object textures')

        # multiview configuration (if implemented)
        self.add_param('multiview_setup.mode', '',
                       'Selected mode to generate view points, i.e., random, bezier, viewsphere')
        self.add_param('multiview_setup.mode_config', Configuration(), 'Mode specific configuration')
        self.add_param('multiview_setup.offset', True,
                       'If False, multi views are not offset with initial camera location. Default: True')
        
        # specific debug config
        self.add_param('debug.plot', False, 'If True, in debug mode, enable simple visual debug')
        self.add_param('debug.plot_axis', False, 'If True, in debug-plot mode, plot camera coordinate systems')
        self.add_param('debug.scatter', False, 'If True, in debug mode-plot, enable scatter plot')
        self.add_param('debug.save_to_blend', False, 'If True, in debug mode, log to .blend files')


@abr_scenes.register(name=_scene_name, type='scene')
class StaticScene(interfaces.IScene):

    def __init__(self, **kwargs):
        super(StaticScene, self).__init__()
        self.logger = get_logger()

        # we do composition here, not inheritance anymore because it is too
        # limiting in its capabilities. Using a render manager is a better way
        # to handle compositor nodes
        self.renderman = abr_scenes.RenderManager()

        # extract configuration, then build and activate a split config
        self.config = kwargs.get('config', StaticSceneConfiguration())
        # this check that the given configuration is (or inherits from) of the correct type
        if not isinstance(self.config, StaticSceneConfiguration):
            raise RuntimeError(f"Invalid configuration of type {type(self.config)} for class {_scene_name}")
        
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
            self.config.render_setup.samples,
            self.config.render_setup.motion_blur)

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
            camera_base_path = f"{self.config.dataset.base_path}/{cam}"
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

    def setup_compositor(self):
        self.renderman.setup_compositor(self.objs, color_depth=self.config.render_setup.color_depth)

    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)

    def setup_textured_objects(self):
        # get list of textures
        self.objects_textures = get_environment_textures(self.config.scenario_setup.objects_textures)
        # check whether given objects exists
        for name in self.config.scenario_setup.textured_objects:
            if bpy.data.objects.get(name) is None:
                self.logger.warn(f'Given object {name} not among available object in the scene. Popping!')
                self.config.scenario_setup.textured_objects.remove(name)

    def randomize_environment_texture(self):
        # set some environment texture, randomize, and render
        env_txt_filepath = expandpath(random.choice(self.environment_textures))
        self.renderman.set_environment_texture(env_txt_filepath)

    def randomize_textured_objects_textures(self):
        for obj_name in self.config.scenario_setup.textured_objects:
            obj_txt_filepath = expandpath(random.choice(self.objects_textures))
            self.renderman.set_object_texture(obj_name, obj_txt_filepath)

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
                config=self.config.multiview_setup.mode_config,
                offset=self.config.multiview_setup.offset)

        else:
            raise ValueError(f'Selected render mode {self.render_mode} not currently supported')
       
        # some debug options
        # NOTE: at this point the object of interest have been loaded in the blender
        # file but their positions have not yet been randomized..so they should all be located
        # at the origin
        if self.config.debug.enabled:
            # simple plot of generated camera locations
            if self.config.debug.plot:
                from amira_blender_rendering.math.curves import plot_points

                for cam_name in camera_names:
                    plot_points(np.array(cameras_locations[cam_name]),
                                bpy.context.scene.objects[cam_name],
                                plot_axis=self.config.debug.plot_axis,
                                scatter=self.config.debug.scatter)

            # save all generated camera locations to .blend for later debug
            if self.config.debug.save_to_blend:
                for i_cam, cam_name in enumerate(camera_names):
                    self.save_to_blend(
                        self.dirinfos[i_cam],
                        camera_name=cam_name,
                        camera_locations=cameras_locations[cam_name],
                        basefilename='robottable_camera_locations')

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
                for cam_name, cam_locations in cameras_locations.items():
                    repeat_frame = not self.test_visibility(cam_name, cam_locations)

            # if we need to repeat (change static scene) we skip one iteration
            # without increasing the counter
            if repeat_frame:
                self.logger.error('Something wrong (possibly due to visibility configurations).'
                                  ' Make sure your static scene and config are correct. Exiting!')
                exit(-1)

            # loop over cameras
            for i_cam, cam_str in enumerate(self.config.scene_setup.cameras):
                # get bpy object camera name
                cam_name = self.get_camera_name(cam_str)

                # check whether we broke the for-loop responsible for image generation for
                # multiple camera views and repeat the frame by re-generating the static scene
                if repeat_frame:
                    # retry at most 'max_retry' times then exit
                    if retry < MAX_RETRY:
                        break
                    self.logger.error(f'Max num of {MAX_RETRY} retry reached. Check your static scene is correct. Exit')
                    exit(-1)
        
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
                            self.config.camera_info.zeroing,
                            postprocess_config=self.config.postprocess)
                        
                        if self.config.debug.enabled and self.config.debug.save_to_blend:
                            # reset frame to 0 and save
                            bpy.context.scene.frame_set(0)
                            self.save_to_blend(
                                self.dirinfos[i_cam],
                                scene_index=scn_counter,
                                view_index=view_counter,
                                basefilename='robottable')

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
