#!/usr/bin/env python

"""
This file implements generation of datasets for workstation scenarios. The file
depends on a suitable workstation scenarion blender file such as
worstationscenarios.blend.
"""

import bpy
from mathutils import Vector
import time
import numpy as np
import random
from math import ceil, log

from amira_blender_rendering import camera_utils
from amira_blender_rendering.utils import expandpath
from amira_blender_rendering.datastructures import Configuration
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.blender_utils as blender_utils
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info


class WorkstationScenariosConfiguration(Configuration):
    """This class specifies all configuration options for WorkstationScenarios"""

    def __init__(self):
        super(WorkstationScenariosConfiguration, self).__init__(name="WorkstationScenarios")

        # general dataset configuration
        self.add_param('dataset.image_count', 1, 'Number of images to generate')
        self.add_param('dataset.base_path', '', 'Path to storage directory')

        # camera configuration
        self.add_param('camera_info.name', 'Pinhole Camera', 'Name for the camera')
        self.add_param('camera_info.model', 'pinhole', 'Camera model type')
        self.add_param('camera_info.width', 640, 'Rendered image resolution (pixel) along x (width)')
        self.add_param('camera_info.height', 480, 'Rendered image resolution (pixel) along y (height)')
        self.add_param('camera_info.k', [], 'calibration matrix K', special='maybe_list')

        # render configuration
        self.add_param('render_setup.backend', 'blender-cycles', 'Render backend. Blender only one supported')
        self.add_param('render_setup.integrator', 'BRANCHED_PATH', 'Integrator used during path tracing. Either of PATH, BRANCHED_PATH')
        self.add_param('render_setup.denoising', True, 'Use denoising algorithms during rendering')
        self.add_param('render_setup.samples', 128, 'Samples to use during rendering')

        # scene configuration
        self.add_param('scene_setup.blend_file', '~/gfx/modeling/workstation_scenarios.blend', 'Path to .blend file with modeled scene')
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images', 'Path to background images / environment textures')
        self.add_param('scene_setup.cameras', ['CameraLeft', 'Camera', 'CameraRight'], 'Cameras to render')
        self.add_param('scene_setup.forward_frames', 15, 'Number of frames in physics forward-simulation')

        # scenario configuration
        self.add_param('scenario_setup.scenario', 0, 'Scenario to render')
        self.add_param('scenario_setup.target_objects', [], 'List of all target objects to drop in environment')



class WorkstationScenarios():
    """base class for all workstation scenarios"""

    def __init__(self, **kwargs):
        super(WorkstationScenarios, self).__init__()

        # extract configuration
        self.config = kwargs.get('config', WorkstationScenariosConfiguration())

        # we do composition here, not inheritance anymore because it is too
        # limiting in its capabilities. Using a render manager is a better way
        # to handle compositor nodes
        self.renderman = abr_scenes.RenderManager()

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

        # populate the scene with objects
        self.setup_objects()

        # finally, setup the compositor
        self.setup_compositor()


    def setup_dirinfo(self):
        """Setup directory information for all cameras.

        This will be required to setup all path information in compositor nodes
        """
        # compute directory information for each of the cameras
        self.dirinfos = []
        for cam in self.config.scene_setup.cameras:
            # paths are set up as: base_path + Scenario## + CameraName
            camera_base_path = f"{self.config.dataset.base_path}-Scenario{self.config.scenario_setup.scenario:02}-{cam}"
            dirinfo = build_directory_info(camera_base_path)
            self.dirinfos.append(dirinfo)

    def setup_scene(self):
        """Set up the entire scene.

        Here, we simply load the main blender file from disk.
        """
        bpy.ops.wm.open_mainfile(filepath=expandpath(self.config.scene_setup.blend_file))


    def setup_cameras(self):
        """Set up all cameras.

        Note that this does not select a camera for which to render. This will
        be selected elsewhere.
        """

        # setup render output dimensions. This is not set for a specific camera,
        # but in renders render environment
        bpy.context.scene.render.resolution_x = self.config.camera_info.width
        bpy.context.scene.render.resolution_y = self.config.camera_info.height

        # set up cameras from calibration information (if any)
        if self.config.camera_info.k is None or len(self.config.camera_info.k) <= 0:
            return

        # convert the configuration value of K to a numpy format
        if isinstance(self.config.camera_info.k, str):
            K = np.fromstring(self.config.camera_info.k, sep=',', dtype=np.float32).reshape((3, 3))
        elif isinstance(self.config.camera_info.k, list):
            K = np.asarray(self.config.camera_info.k, dtype=np.float32).reshape((3, 3))
        else:
            raise RuntimeError("invalid value for camera_info.k")

        for cam in self.config.scene_setup.cameras:
            # first get the camera name. this depends on the scene (blend file)
            # and is of the format CameraName.XXX, where XXX is a number with
            # leading zeros
            cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
            # select the camera. Blender often operates on the active object, to
            # make sure that this happens here, we select it
            blender_utils.select_object(cam_name)
            # modify camera according to K
            blender_camera = bpy.context.scene.objects[cam_name]
            camera_utils.opencv_to_blender(K, blender_camera)


    def setup_objects(self):
        """This method populates the scene with objects.

        Object types and number of objects will be taken from the configuration.
        The format to specify objects is
            ObjectType:Number
        where ObjectType should be the name of an object that exists in the
        blender file, and number indicates how often the object shall be
        duplicated.
        """
        # let's start with an empty list
        self.objs = []

        # extract all objects from the configuration. An object has a certain
        # type, as well as an own id. this information is storeed in the objs
        # list, which contains a dict. The dict contains the following keys:
        #       id_mask     used for mask computation, computed below
        #       model_name  type-name of the object
        #       model_id    model type ID (simply incremental numbers)
        #       object_id   instance ID of the object
        #       bpy         blender object reference
        n_types = 0      # count how many types we have
        n_instances = [] # count how many instances per type we have
        for model_id, obj_spec in enumerate(self.config.scenario_setup.target_objects):
            obj_type, obj_count = obj_spec.split(':')
            n_types += 1
            n_instances.append(int(obj_count))
            for j in range(int(obj_count)):
                # duplicate proto-object
                blender_utils.select_object(obj_type)
                bpy.ops.object.duplicate()
                new_obj = bpy.context.object

                # append all information
                self.objs.append({
                        'id_mask': '',
                        'model_name': obj_type,
                        'model_id': model_id,
                        'object_id': j,
                        'bpy': new_obj
                    })

        # build masks id for compositor of the format _N_M, where N is the model
        # id, and M is the object id
        m_w = ceil(log(n_types))  # format width for number of model types
        for i, obj in enumerate(self.objs):
            o_w = ceil(log(n_instances[obj['model_id']]))   # format width for number of objects of same model
            id_mask = f"_{obj['model_id']:0{m_w}}_{obj['object_id']:0{o_w}}"
            obj['id_mask'] = id_mask


    def setup_compositor(self):
        self.renderman.setup_compositor(self.objs)


    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_texture)


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
        print(f"II: forward simulation of {self.config.scene_setup.forward_frames} frames")
        scene = bpy.context.scene
        for i in range(self.config.scene_setup.forward_frames):
            scene.frame_set(i+1)

    def activate_camera(self, cam:str):
        # first get the camera name. this depends on the scene (blend file)
        # and is of the format CameraName.XXX, where XXX is a number with
        # leading zeros
        cam_name = f"{cam}.{self.config.scenario_setup.scenario:03}"
        bpy.context.scene.camera = bpy.context.scene.objects[cam_name]


    def generate_dataset(self):
        """This will generate the dataset according to the configuration that
        was passed in the constructor.
        """

        # NOTE: this is mostly taken and adapted from
        #       scripts/render_dataset_RenderedObjects.py

        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        format_width = int(ceil(log(image_count, 10)))

        i = 0
        while i < self.config.dataset.image_count:
            # generate render filename
            base_filename = "{:0{width}d}".format(i, width=format_width)

            # randomize scene: move objects at random locations, and forward
            # simulate physics
            self.randomize_environment_texture()
            self.randomize_object_transforms()
            self.forward_simulate()

            # loop through all cameras
            repeat_frame = False
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
                    self.renderman.postprocess(self.dirinfos[i_cam], base_filename, bpy.context.scene.camera, self.objs)
                except ValueError:
                    # This issue happens every now and then. The reason might be (not
                    # yet verified) that the target-object is occluded. In turn, this
                    # leads to a zero size 2D bounding box...
                    print(f"ValueError during post-processing, re-generating image index {i}")
                    repeat_frame = True

                    # no need to continue with other cameras
                    break

            # if we need to repeat this frame, then do not increment the counter
            if not repeat_frame:
                i = i + 1

        return True
