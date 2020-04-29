#!/usr/bin/env python

# blender
import bpy
from mathutils import Vector, Matrix
import os
from math import ceil, log
import random
import numpy as np

from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
from amira_blender_rendering.datastructures import flatten
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom
import amira_blender_rendering.interfaces as interfaces



class SimpleToolCapConfiguration(abr_scenes.BaseConfiguration):
    def __init__(self):
        super(SimpleToolCapConfiguration, self).__init__()

        # scene specific configuration
        # let's be able to specify environment textures
        self.add_param('scene_setup.environment_textures', '$AMIRA_DATASETS/OpenImagesV4/Images', 'Path to background images / environment textures')



class SimpleToolCap(interfaces.ABRScene):
    """Simple toolcap scene in which we have three point lighting and can set
    some background image.
    """
    def __init__(self, **kwargs):
        super(SimpleToolCap, self).__init__()
        self.logger = get_logger()

        # we make use of the RenderManager
        self.renderman = abr_scenes.RenderManager()

        # get the configuration, if one was passed in
        self.config = kwargs.get('config', SimpleToolCapConfiguration())
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
                self.config.render_setup.samples)

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
        # convert all scaling factors from str to list of floats
        if 'ply_scale' not in self.config.parts:
            return

        for part in self.config.parts.ply_scale:
            vs = self.config.parts.ply_scale[part]
            vs = [v.strip() for v in vs.split(',')]
            vs = [float(v) for v in vs]
            self.config.parts.ply_scale[part] = vs


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


    def setup_lighting(self):
        # this scene uses classical three point lighting
        self.setup_three_point_lighting()


    def setup_cameras(self):
        """Setup camera, and place at a default location"""

        # add camera, update with calibration data, and make it active for the scene
        bpy.ops.object.add(type='CAMERA', location=(0.66, -0.66, 0.5))
        self.cam_obj = bpy.context.object
        self.cam = self.cam_obj.data
        if self.config.camera_info.intrinsic is not None:
            self.logger.info("Using camera calibration data")
            if isinstance(self.config.camera_info.intrinsic, str):
                intrinsics = np.fromstring(self.config.camera_info.intrinsic, sep=',', dtype=np.float32)
            elif isinstance(self.config.camera_info.intrinsic, list):
                intrinsics = np.asarray(self.config.camera_info.intrinsic, dtype=np.float32)
            else:
                raise RuntimeError("invalid value for camera_info.intrinsics")
            self.cam = camera_utils.set_intrinsics(bpy.context.scene, self.cam,
                    intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3])

        # re-set camera and set rendering size
        bpy.context.scene.camera = self.cam_obj
        bpy.context.scene.render.resolution_x = self.config.camera_info.width
        bpy.context.scene.render.resolution_y = self.config.camera_info.height

        # look at center
        blnd.look_at(self.cam_obj, Vector((0.0, 0.0, 0.0)))


    def setup_objects(self):
        # the order of what's done is important. first import and setup the
        # object and its material, then rescale it. otherwise, values from
        # shader nodes might not reflect the correct sizes (the metal-tool-cap
        # material depends on an empty that is placed on top of the object.
        # scaling the empty will scale the texture)
        self._import_mesh()
        self._setup_material()
        self._rescale_objects()

        # we also need to create a dictionary with the object for the compositor
        # to do its job, as well as the annotation generation
        self.objs = list()
        self.objs.append({
            'id_mask': '_0_0',        # the format of the masks is usually _modelid_objectid
            'model_name': 'Tool.Cap', # model name is hardcoded here
            'model_id': 0,            # we only have one model type, so id = 0
            'object_id': 0,           # we only have this single instance, so id = 0
            'bpy': self.obj})         # also add reference to the blender object


    def setup_compositor(self):
        # we let renderman handle the compositor. For this, we need to pass in a
        # list of objects
        self.renderman.setup_compositor(self.objs)

    def setup_environment_textures(self):
        # get list of environment textures
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)


    def _rescale_objects(self):
        self.obj.scale = Vector(self.config.parts.ply_scale.tool_cap)


    def _import_mesh(self):
        """Import the mesh of the cap from a ply file."""
        path = expandpath(self.config.parts.ply.tool_cap)
        bpy.ops.import_mesh.ply(filepath=path)
        self.obj = bpy.context.object
        self.obj.name = 'Tool.Cap'


    def _setup_material(self):
        """Setup object material"""

        # make sure cap is selected
        blnd.select_object(self.obj.name)

        # remove any material that's currently assigned to the object and then
        # setup the metal for the cap
        blnd.remove_material_nodes(self.obj)
        blnd.clear_orphaned_materials()

        # add default material and setup nodes (without specifying empty, to get
        # it created automatically)
        self.cap_mat = blnd.add_default_material(self.obj)
        abr_nodes.material_metal_tool_cap.setup_material(self.cap_mat)


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
        if not os.path.exists(self.dirinfo.base_path):
                os.mkdir(self.dirinfo.base_path)
        dump_config(self.config, self.dirinfo.base_path)


    def generate_dataset(self):
        # filename setup
        image_count = self.config.dataset.image_count
        if image_count <= 0:
            return False
        format_width = int(ceil(log(image_count, 10)))

        i = 0
        while i < self.config.dataset.image_count:
            # generate render filename
            base_filename = "{:0{width}d}".format(i, width=format_width)

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
                self.renderman.postprocess(self.dirinfo, base_filename,
                        bpy.context.scene.camera, self.objs,
                        self.config.camera_info.zeroing)
            except ValueError:
                self.logger.warn("ValueError during post-processing, re-generating image index {i}")
            else:
                i = i + 1

        return True


    def generate_viewsphere_dataset(self):
        raise NotImplementedError()


    def teardown(self):
        pass
