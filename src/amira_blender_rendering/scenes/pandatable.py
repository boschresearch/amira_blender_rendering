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
from amira_blender_rendering.math.curves import points_on_bezier, points_on_circle, points_on_wave, plot_points
from amira_blender_rendering.datastructures import Configuration


class PandaTableConfiguration(abr_scenes.BaseConfiguration):
    """This class specifies all configuration options for the Panda Table scenario."""

    def __init__(self):
        super(PandaTableConfiguration, self).__init__()

        # specific scene configuration
        self.add_param('scene_setup.blend_file', '~/gfx/modeling/robottable_empty.blend', 'Path to .blend file with modeled scene')
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images', 'Path to background images / environment textures')
        self.add_param('scene_setup.cameras', ['Camera,' 'StereoCamera.Left', 'StereoCamera.Right', 'Camera.FrontoParallel.Left', 'Camera.FrontoParallel.Right'], 'Cameras to render')
        self.add_param('scene_setup.forward_frames', 25, 'Number of frames in physics forward-simulation')

        # scenario: target objects
        self.add_param('scenario_setup.target_objects', [], 'List of all target objects to drop in environment')
        self.add_param('scenario_setup.non_target_objects', [], 'List of objects visible in the scene but of which infos are not stored')
        
        # multiview configuration (if implemented)
        self.add_param('scenario_setup.multiview.cameras', [], 'Cameras to render in multiview setup')
        self.add_param('scenario_setup.multiview.view_count', 0, 'Number of view points, i.e., camera locations')
        self.add_param('scenario_setup.multiview.mode', '', 'Selected mode to generate view points, i.e., random, bezier, viewsphere')
        self.add_param('scenario_setup.multiview.mode_config', Configuration(), 'Mode specific configuration')
        self.add_param('scenario_setup.multiview.allow_occlusions', False, 'If True, target objects visibility is not tested')


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
        if self.config.dataset.scene_type.lower() != 'PandaTable'.lower():
            raise RuntimeError(f"Invalid configuration of scene type {self.config.dataset.scene_type} for class PandaTable")

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
        self.objs = self.setup_objects(self.config.scenario_setup.target_objects)
        self.nt_objs = self.setup_objects(self.config.scenario_setup.non_target_objects)

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
        cam = bpy.data.objects[f'{cam_str}'].data

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
            cam_name = f"{cam}"
            # select the camera. Blender often operates on the active object, to
            # make sure that this happens here, we select it
            blnd.select_object(cam_name)
            # modify camera according to the intrinsics
            blender_camera = bpy.data.objects[cam_name].data
            # set the calibration matrix
            camera_utils.set_camera_info(scene, blender_camera, self.config.camera_info)


    def setup_objects(self, target_objects):
        """This method populates the scene with objects.

        Object types and number of objects will be taken from the configuration.
        The format to specify objects is
            ObjectType:Number
        where ObjectType should be the name of an object that exists in the
        blender file, and number indicates how often the object shall be
        duplicated.
        
        Args:
            target_objects(list): list of ObjectType:Number to setup

        Returns:
            objs(list): list of dict to handle desired objects
        """
        # let's start with an empty list
        objs = []

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
        n_types = 0       # count how many types we have
        n_instances = []  # count how many instances per type we have
        for obj_type_id, obj_spec in enumerate(target_objects):
            obj_type, obj_count = obj_spec.split(':')
            n_types += 1
            n_instances.append(int(obj_count))

            # here we distinguish if we copy a part from the proto objects
            # within a scene, or if we have to load it from file
            is_proto_object = not obj_type.startswith('parts.')
            if not is_proto_object:
                # split off the prefix for all files that we load from blender
                obj_type = obj_type[6:]

            # TODO: file loading happens only very late in this loop. This might
            #       be an issue for large object counts and could be changed to
            #       load-once copy-often.
            for j in range(int(obj_count)):
                # First, deselect everything
                bpy.ops.object.select_all(action='DESELECT')
                if is_proto_object:
                    # duplicate proto-object
                    blnd.select_object(obj_type)
                    bpy.ops.object.duplicate()
                    new_obj = bpy.context.object
                else:
                    # we need to load this object from file. This could be
                    # either a blender file, or a PLY file
                    blendfile = expandpath(self.config.parts[obj_type], check_file=False)
                    if os.path.exists(blendfile):
                        # this is a blender file, so we should load it
                        # we can now load the object into blender
                        blnd.append_object(blendfile, obj_type)
                        # NOTE: bpy.context.object is **not** the object that we are
                        # interested in here! We need to select it via original name
                        # first, then we rename it to be able to select additional
                        # objects later on
                        new_obj = bpy.data.objects[obj_type]
                        new_obj.name = f'{obj_type}.{j:03d}'
                    else:
                        # no blender file given, so we will load the PLY file
                        ply_path = expandpath(self.config.parts.ply[obj_type], check_file=True)
                        bpy.ops.import_mesh.ply(filepath=ply_path)
                        # here we can use bpy.context.object!
                        new_obj = bpy.context.object
                        new_obj.name = f'{obj_type}.{j:03d}'

                # move object to collection
                collection = bpy.data.collections['TargetObjects']
                if new_obj.name not in collection.objects:
                    collection.objects.link(new_obj)

                # append all information
                objs.append({
                    'id_mask': '',
                    'object_class_name': obj_type,
                    'object_class_id': obj_type_id,
                    'object_id': j,
                    'bpy': new_obj,
                    'visible': None
                })

        # build masks id for compositor of the format _N_M, where N is the model
        # id, and M is the object id
        m_w = ceil(log(n_types)) if n_types else 0  # format width for number of model types
        for i, obj in enumerate(objs):
            o_w = ceil(log(n_instances[obj['object_class_id']]))   # format width for number of objects of same model
            id_mask = f"_{obj['object_class_id']:0{m_w}}_{obj['object_id']:0{o_w}}"
            obj['id_mask'] = id_mask
        
        return objs


    def setup_compositor(self):
        self.renderman.setup_compositor(self.objs)


    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)


    def randomize_object_transforms(self, objs: list):
        """move all objects to random locations within their scenario dropzone,
        and rotate them.
        
        Args:
            objs(list): list of objects whose pose is randomized.

        NB: the list of objects must be mutable since the method does not return but directly modify them!
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
            scene.frame_set(i+1)


    def activate_camera(self, cam: str):
        # first get the camera name. this depends on the scene (blend file)
        # and is of the format CameraName.XXX, where XXX is a number with
        # leading zeros
        cam_name = f"{cam}"
        bpy.context.scene.camera = bpy.context.scene.objects[cam_name]
        camera = bpy.context.scene.camera
        return camera


    def generate_multiview_cameras_locations(self, **kw):

        def get_array_from_str(cfg, name, default):
            p = cfg.get(name, default)
            if isinstance(p, str):
                p = np.fromstring(p, sep=',')
            return p

        # init container
        locations = {}
        original_locations = {}

        # additional configs to control specific mode
        mode_cfg = kw.get('config', Configuration())

        view_count = self.config.scenario_setup.multiview.view_count

        # loop over cameras
        for cam_name in self.config.scenario_setup.multiview.cameras:

            # log
            self.logger.info(f'Generating locations according to {self.config.scenario_setup.multiview.mode} mode')

            # extract camera object
            camera = bpy.context.scene.objects[cam_name]

            # init camera location list and store original
            locations[cam_name] = []
            original_locations[cam_name] = np.asarray(camera.matrix_world.to_translation())
                 
            if self.config.scenario_setup.multiview.mode == 'random':

                cam_loc0 = get_array_from_str(mode_cfg, 'start_location', original_locations[cam_name])
                scale = float(mode_cfg.get('scale', 1))
                vc = 0
                while vc < view_count:
                    p = cam_loc0 + scale * np.random.randn(cam_loc0.size)
                    # check if occlusions are allowed
                    if not self.config.scenario_setup.multiview.allow_occlusions:
                        # if not, test for visibility
                        if not self.test_multiview_visibility(camera, [p]):
                            # if not visible, generate new p
                            continue
                    locations[cam_name].append(p)
                    vc = vc + 1

                # since either we checked all the positions or it does not matter,
                # repeat frame is always False
                repeat_frame = False

                # for visual debug
                if self.config.logging.debug:
                    plot_points(np.array(locations[cam_name]), camera, plot_axis=bool(self.config.logging.plot_axis))


            elif self.config.scenario_setup.multiview.mode == 'bezier':
                # Define control points for bezier curve
                # here it is assumed to cameras have an aiming point to a empty in blender.
                # Hence, by changing the location, the cameras should automatically
                # adjust their orientation
                start = float(mode_cfg.get('start', 0))
                stop = float(mode_cfg.get('stop', 1))
                p0 = get_array_from_str(mode_cfg, 'p0', original_locations[cam_name])
                p1 = get_array_from_str(mode_cfg, 'p1', p0 + np.random.randn(p0.size))
                p2 = get_array_from_str(mode_cfg, 'p2', p0 + np.random.randn(p0.size))
                
                locations[cam_name] = points_on_bezier(view_count, p0, p1, p2, start, stop)

                # for visual debug
                if self.config.logging.debug:
                    plot_points(np.array(locations[cam_name]), camera, plot_axis=bool(self.config.logging.plot_axis))
                
                repeat_frame = False
                if not self.config.scenario_setup.multiview.allow_occlusions:
                    repeat_frame = not self.test_multiview_visibility(camera, locations[cam_name])

            elif self.config.scenario_setup.multiview.mode == 'circle':
                # extract config
                r = float(mode_cfg.get('radius', 1))
                c = get_array_from_str(mode_cfg, 'center', original_locations[cam_name])
                locations[cam_name] = points_on_circle(view_count, r, c)

                # for visual debug
                if self.config.logging.debug:
                    plot_points(np.array(locations[cam_name]), camera, plot_axis=bool(self.config.logging.plot_axis))

                repeat_frame = False
                if not self.config.scenario_setup.multiview.allow_occlusions:
                    repeat_frame = not self.test_multiview_visibility(camera, locations[cam_name])

            elif self.config.scenario_setup.multiview.mode == 'wave':
                r = float(mode_cfg.get('radius', 1))
                c = get_array_from_str(mode_cfg, 'center', original_locations[cam_name])
                w = float(mode_cfg.get('frequency', 1))
                A = float(mode_cfg.get('amplitude', 1))
                locations[cam_name] = points_on_wave(view_count, r, c, w, A)

                # for visual debug
                if self.config.logging.debug:
                    plot_points(np.array(locations[cam_name]), camera, plot_axis=bool(self.config.logging.plot_axis))

                repeat_frame = False
                if not self.config.scenario_setup.multiview.allow_occlusions:
                    repeat_frame = not self.test_multiview_visibility(camera, locations[cam_name])


            elif self.config.scenario_setup.multiview.mode == 'viewsphere':
                raise NotImplementedError

            else:
                raise ValueError('Selected mode {self.config.scenario_setup.multiview.mode} not supported for multiview locations')

        return locations, original_locations, repeat_frame


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


    def test_multiview_visibility(self, camera, locations):
        """Test visibility of target object from camera locations

        Args:
            camera(bpy.objects.camera): camera object
            locations(list): list of locations for camera
        
        Returns:
            True if target objects are visible. False otherwise.
        """
        for location in locations:
            camera.location = location
            if not self.test_single_camera_visibility(camera):
                return False
        return True


    def test_visibility(self):
        """Test visibility for target object from all fixed camera in the scene"""
        for i_cam, cam in enumerate(self.config.scene_setup.cameras):
            cam_name = f"{cam}"
            cam_obj = bpy.data.objects[cam_name]
            # If at least one camera fails, visibility fails
            if not self.test_single_camera_visibility(cam_obj):
                return False
        return True


    def test_single_camera_visibility(self, camera):
        """Test whether given camera sees all target objects
        and store visibility level/label for each target object"""
        # TODO: can we distinguish among full visibility, partial visibility and complete occlusion?
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
            
            obj['visible'] = True

            if not_visible_or_occluded:
                self.logger.warn(f"object {obj} not visible or occluded")
                obj['visible'] = False
                if self.config.logging.debug:
                    self.logger.info(f"saving blender file for debugging to /tmp/robottable.blend")
                    bpy.ops.wm.save_as_mainfile(filepath="/tmp/robottable.blend")
        
            # keep trace if any obj was not visible or occluded
            any_not_visible_or_occluded = any_not_visible_or_occluded or not_visible_or_occluded

        if any_not_visible_or_occluded:
            return False
        return True


    def postprocess_multiview_config(self):
        """
        Make sure the config for scenario_setup.multiview are correct
        """
        # check cameras
        if not self.config.scenario_setup.multiview.cameras:
            raise ValueError('[Multiview rendering] at least one camera must be selected.')
        for cam in self.config.scenario_setup.multiview.cameras:
            if cam not in self.config.scene_setup.cameras:
                raise ValueError('[Multiview rendering] Selected camera {cam} not is list of available cameras')
        # check view count
        if self.config.scenario_setup.multiview.view_count <= 0:
            self.config.scenario_setup.multiview.view_count = 1


    def generate_multiview_dataset(self):
        """This will generate a multiview dataset according to the configuration that
        was passed in the constructor.
        """
        # The multiview dataset is controlled by multiple options
        # As for standard dataset
        #
        #   dataset.image_count
        #
        # controls the number of scenes that are rendered (objects in different poses)
        # per each configuration (if multiple are defined).
        # In addition the [multiview] config section defines specific configuration such as
        #
        #   [multiview]
        #   cameras(list): defines the cameras (subset of scene_setup.cameras) that are rendered in multiview
        #   view_count(int): defines the (minimum) number of camera locations (different views of a static scene)
        #   mode(str): how to generate camera locations for multiview. E.g., viewsphere, bezier, random

        # check basic multiview config
        self.postprocess_multiview_config()

        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        scn_format_width = int(ceil(log(image_count, 10)))
        
        # control loop for the number of static scenes to render
        ic = 0
        original_cam_locs = None
        while ic < image_count:

            # randomize scene: move objects at random locations, and forward simulate physics
            self.randomize_environment_texture()
            # first drop non target objects which are visible in the scene
            self.randomize_object_transforms(self.nt_objs)
            self.forward_simulate()
            # then drop targets
            self.randomize_object_transforms(self.objs)
            self.forward_simulate()

            # since multiview locations might be camera dependant,
            # restore original locations if we changed them during previous iteration
            if original_cam_locs is not None:
                for cam_name in self.config.scenario_setup.multiview.cameras:
                    camera = bpy.context.scene.objects[cam_name]
                    camera.location = original_cam_locs[cam_name]
                # update depsgraph
                bpy.context.evaluated_depsgraph_get().update()

            # generate views for current static scene
            multiview_cam_locs, original_cam_locs, repeat_frame = self.generate_multiview_cameras_locations(
                config=self.config.scenario_setup.multiview.mode_config
            )

            # if we need to repeat (change static scene) we skip one iteration
            # without increasing the counter
            if repeat_frame:
                self.logger.warn(f'Something wrong. Re-randomizing scene {ic + 1}/{image_count}')
                continue

            # loop over cameras
            for cam_name in self.config.scenario_setup.multiview.cameras:
                # extract camera index
                i_cam = self.config.scene_setup.cameras.index(cam_name)
                
                # extract camera locations
                camera_locations = multiview_cam_locs[cam_name]
                
                # compute format width
                view_format_width = int(ceil(log(len(camera_locations), 10)))
                
                # activate camera
                camera = self.activate_camera(cam_name)

                # loop over locations
                for vc, cam_loc in enumerate(camera_locations):

                    self.logger.info(
                        f"Generating image: scene {ic + 1}/{image_count}, view {vc + 1}/{self.config.scenario_setup.multiview.view_count}")

                    # filename
                    base_filename = "s{:0{width}d}_v{:0{cam_width}d}".format(ic, vc,
                                                                             width=scn_format_width,
                                                                             cam_width=view_format_width)

                    # set camera location
                    self.set_camera_location(cam_name, cam_loc)

                    # at this point all the locations have already been tested for visibility
                    # according to allow_occlusions config.
                    # Here, we re-run visibility to set object visibility level as well as to update
                    # the depsgraph needed to update translation and rotation info
                    self.test_single_camera_visibility(camera)

                    # update path information in compositor
                    self.renderman.setup_pathspec(self.dirinfos[i_cam], base_filename, self.objs)
                    
                    # finally, render
                    self.renderman.render()

                    # postprocess. this will take care of creating additional
                    # information, as well as fix filenames
                    # try-catch similar to generate_dataset (see below)
                    # TODO: the try catch should not be necessary anymore
                    try:
                        self.renderman.postprocess(
                            self.dirinfos[i_cam],
                            base_filename,
                            bpy.context.scene.camera,
                            self.objs,
                            self.config.camera_info.zeroing,
                            rectify_depth=self.config.postprocess.rectify_depth,
                            overwrite=self.config.postprocess.overwrite)
                    except ValueError:
                        self.logger.error(f"\033[1;31mValueError during post-processing, re-generating image {ic + 1}/{image_count}\033[0;37m")
                        repeat_frame = True
                        break

            # update scene counter
            if not repeat_frame:
                ic = ic + 1

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
            self.logger.info(f"Generating image {i+1} of {self.config.dataset.image_count}")

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
                self.logger.warn(f"\033[1;33mObject(s) not visible from every camera. Re-randomizing... \033[0;37m")
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
                        self.renderman.postprocess(
                            self.dirinfos[i_cam],
                            base_filename,
                            bpy.context.scene.camera, self.objs,
                            self.config.camera_info.zeroing,
                            rectify_depth=self.config.postprocess.rectify_depth,
                            overwrite=self.config.postprocess.overwrite)
                    except ValueError:
                        # This issue happens every now and then. The reason might be (not
                        # yet verified) that the target-object is occluded. In turn, this
                        # leads to a zero size 2D bounding box...
                        self.logger.error(f"\033[1;31mValueError during post-processing, re-generating image index {i}\033[0;37m")
                        repeat_frame = True

                        # no need to continue with other cameras
                        break

            # if we need to repeat this frame, then do not increment the counter
            if not repeat_frame:
                i = i + 1

        return True
