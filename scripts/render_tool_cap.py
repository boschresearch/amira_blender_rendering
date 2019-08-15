#!/usr/bin/env python

# make amira_deep_vision packages available
import sys, os
import bpy
import numpy as np
from math import ceil, log
from mathutils import Vector

#
# ---- Configuration starts here
# TODO: move to a configuration file that we can directly import, and also
# change single environment texture to load arbitrary files
#

APS_REPOSITORY_PATH = '~/dev/vision/amira_deep_vision'
APS_RENDERED_OBJECTS_STATIC_METHODS = 'aps/data/datasets/renderedobjects_static.py'
AMIRA_BLENDER_PATH = '~/dev/vision/amira_blender_rendering/src'

OUTPUT_PATH = '/tmp/BlenderRenderedObjects'
ENVIRONMENT_TEXTURE = '~/gfx/assets/hdri/small_hangar_01_4k.hdr'

N_IMAGES = 100

#
# ---- Configuration ends here
#


# make amira_blender_rendering and aps importable
sys.path.append(os.path.expanduser(APS_REPOSITORY_PATH))
sys.path.append(os.path.expanduser(AMIRA_BLENDER_PATH))

# import blender things
from amira_blender_rendering import utils
from amira_blender_rendering import camera_utils
from amira_blender_rendering import blender_utils as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes

# import amira_deep_vision stuff that is required to generate the output
from aps.core.interfaces import PoseRenderResult

# we cannot import aps.data, because blender<->torch has some gflags issues at
# the moment that we cannot solve. That is, when running blender -c --python
# console, then import torch, leads to an ERROR and blender quits. To circumvent
# this issue, we'll manually import the file that gives us diretory information
# of renderedobjects within the following function. Fore more information, read
# the comment in the file that gets imported
def import_renderedobjects_static_methods():
    import importlib
    try:
        fname = os.path.expanduser(os.path.join(
            APS_REPOSITORY_PATH,
            APS_RENDERED_OBJECTS_STATIC_METHODS))
        spec = importlib.util.spec_from_file_location('renderedobjects_static', fname)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError as e:
        raise RuntimeError(f"Could not import RenderedObjects' static methods")
    return module
ro_static = import_renderedobjects_static_methods()



class SimpleToolCapScene(
        abr_scenes.BaseSceneManager,
        abr_scenes.ThreePointLighting):
    """Simple toolcap scene in which we have three point lighting and can set
    some background image.
    """

    def __init__(self, base_filename: str):
        super(SimpleToolCapScene, self).__init__()
        self.reset()
        self.base_filename = base_filename

        # TODO: pass camera calibration information and scene size as argument
        self.K = np.array([ 9.9801747708520452e+02, 0., 6.6049856967197002e+02, 0., 9.9264009290521165e+02, 3.6404286361152555e+02, 0., 0., 1. ]).reshape(3,3)
        self.width = 1280
        self.height = 720

        # setup blender scene and camera
        self.setup_scene()
        self.setup_camera()
        self.setup_three_point_lighting()
        self.setup_object()
        # compositor setup needs to come after setting up the objects
        self.setup_environment()
        self.setup_compositor()


    def setup_object(self):
        # the order of what's done is important. first import and setup the
        # object and its material, then rescale it. otherwise, values from
        # shader nodes might not reflect the correct sizes (the metal-tool-cap
        # material depends on an empty that is placed on top of the object.
        # scaling the empty will scale the texture)
        self.import_mesh()
        self.setup_material()
        self.rescale_objects()


    def rescale_objects(self):
        # needs to be re-scaled to fit nicely into blender units
        self.cap_obj.scale = Vector((0.010, 0.010, 0.010))


    def import_mesh(self):
        """Import the mesh of the cap from a ply file."""
        # load mesh from assets directory
        self.ply_path = os.path.join(blnd.assets_dir, 'tool_cap.ply')
        bpy.ops.import_mesh.ply(filepath=self.ply_path)
        self.cap_obj = bpy.context.object
        self.cap_obj.name = 'Tool.Cap'


    def select_cap(self):
        """Select the cap, which is the object of interest in this scene."""
        bpy.ops.object.select_all(action='DESELECT')
        self.cap_obj.select_set(state=True)
        bpy.context.view_layer.objects.active = self.cap_obj


    def setup_material(self):
        """Setup object material"""

        # make sure cap is selected
        self.select_cap()

        # remove any material that's currently assigned to the object and then
        # setup the metal for the cap
        blnd.remove_material_nodes(self.cap_obj)
        blnd.clear_orphaned_materials()

        # add default material and setup nodes (without specifying empty, to get
        # it created automatically)
        self.cap_mat = blnd.add_default_material(self.cap_obj)
        abr_nodes.setup_material_nodes_metal_tool_cap(self.cap_mat)


    def setup_compositor(self):
        """Setup output compositor nodes"""
        self.dirinfo = ro_static.build_directory_info(OUTPUT_PATH)
        self.compositor = abr_nodes.CompositorNodesOutputRenderedObject()

        # setup all path related information in the compositor
        # TODO: both in amira_deep_vision as well as here we actually only need
        # some schema that defines the layout of the dataset. This should be
        # extracted into an independent schema file. Note that this does not
        # mean to use any xml garbage! Rather, it should be as plain as
        # possible.
        self.compositor.setup(self.dirinfo, self.base_filename, objs=[self.cap_obj])


    def setup_scene(self):
        """Setup the scene"""
        bpy.context.scene.render.resolution_x = self.width
        bpy.context.scene.render.resolution_y = self.height


    def setup_camera(self):
        """Setup camera, and place at a default location"""

        # add camera and make it active for the scene
        bpy.ops.object.add(type='CAMERA', location=(0.66, -0.66, 0.5))
        self.cam = bpy.context.object
        bpy.context.scene.camera = self.cam

        # update with calibration data (here as an example from Orbbec Astra # Pro)
        self.cam = camera_utils.opencv_to_blender(self.width, self.height, self.K, self.cam)

        # look at center
        blnd.look_at(self.cam, Vector((0.0, 0.0, 0.0)))


    def setup_environment(self):
        # TODO: randomly select a file from directory
        filepath = os.path.expanduser(ENVIRONMENT_TEXTURE)
        self.set_environment_texture(filepath)


    def set_base_filename(self, filename):
        if filename == self.base_filename:
            return
        self.base_filename = filename

        # update the compositor with the new filename
        self.compositor.update(
                self.dirinfo,
                self.base_filename,
                [self.cap_obj])


    def render(self):
        # Rendering will automatically save images due to the compositor node
        # setup. passing write_still=False prevents writing another file
        bpy.ops.render.render(write_still=False)


    def save_annotations(self):
        # TODO: extract PoseRenderResult, and save annotation to json
        pass


    def save_dataset_configuration(self):
        # TODO: save the dataset.cfg file
        pass

    def postprocess(self):
        # the compositor postprocessing takes care of fixing file names
        self.compositor.postprocess()
        self.save_annotations()
        self.save_dataset_configuration()


def main():
    i = 13
    format_width = int(ceil(log(N_IMAGES, 10)))
    base_filename = "{:0{width}d}".format(i, width=format_width)

    blnd.activate_cuda_devices()
    scene = SimpleToolCapScene(base_filename)
    scene.render()
    scene.postprocess()



if __name__ == "__main__":
    main()
