#!/usr/bin/env python

# blender
import bpy
from mathutils import Vector

import os
import numpy as np
import imageio
try:
    import ujson as json
except:
    import json

from amira_blender_rendering import utils
from amira_blender_rendering import camera_utils
from amira_blender_rendering import blender_utils as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom

# import things from AMIRA Perception Subsystem that are required
from aps.core.interfaces import PoseRenderResult
from aps.core.cv.camera import boundingbox_from_mask



class SimpleToolCap(
        abr_scenes.BaseSceneManager,
        abr_scenes.ThreePointLighting):
    """Simple toolcap scene in which we have three point lighting and can set
    some background image.
    """

    def __init__(self, base_filename: str, dirinfo):
        super(SimpleToolCap, self).__init__()
        self.reset()
        self.base_filename = base_filename
        self.dirinfo = dirinfo

        # TODO: pass camera calibration information and scene size as argument,
        #       or read from configuration
        self.K = np.array([ 9.9801747708520452e+02, 0., 6.6049856967197002e+02, 0., 9.9264009290521165e+02, 3.6404286361152555e+02, 0., 0., 1. ]).reshape(3,3)
        self.width = 640
        self.height = 480

        # setup blender scene, camera, object, and compositors.
        # Note that the compositor setup needs to come after setting up the objects
        self.setup_scene()
        self.setup_camera()
        self.setup_three_point_lighting()
        self.setup_object()
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

        # add camera, update with calibration data, and make it active for the scene
        bpy.ops.object.add(type='CAMERA', location=(0.66, -0.66, 0.5))
        self.cam = bpy.context.object
        # self.cam = camera_utils.opencv_to_blender(self.width, self.height, self.K, self.cam)
        bpy.context.scene.camera = self.cam

        # look at center
        blnd.look_at(self.cam, Vector((0.0, 0.0, 0.0)))


    def setup_environment(self):
        # TODO: randomly select a file from directory
        ENVIRONMENT_TEXTURE = '~/gfx/assets/hdri/small_hangar_01_4k.hdr'


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


    def save_annotations(self, corners2d, corners3d, aabb, oobb):
        """Save annotations of a render result."""

        # create a pose render result. leave image fields empty, they will
        # currenlty not go to the state dict. this is only here to make sure
        # that we actually get the state dict defined in pose render result
        t = np.asarray(abr_geom.get_relative_translation(self.cap_obj, self.cam))
        R = np.asarray(abr_geom.get_relative_rotation(self.cap_obj, self.cam).to_matrix())
        render_result = PoseRenderResult('Tool.Cap', None, None, None, None, None, None,
                R, t, corners2d, corners3d, aabb, oobb)

        if not os.path.exists(self.dirinfo.annotations):
            os.mkdir(self.dirinfo.annotations)

        # build json name, dump data
        fname_json = f"{self.base_filename}.json"
        fname_json = os.path.join(self.dirinfo.annotations, f"{fname_json}")
        json_data = render_result.state_dict()
        with open(fname_json, 'w') as f:
            json.dump(json_data, f, indent=0)


    def compute_2dbbox(self):
        """Compute the 2D bounding box around an object.

        This simply loads the file from disk and gets the pixels. Unfortunately,
        it is not possible right now to work around this with using blender's
        viewer nodes. That is, using a viewer node attached to ID Mask nodes
        will store an image only to bpy.data.Images['Viewer Node'], depending on
        which node is currently selected in the node editor... I have yet to find a
        programmatic way that circumvents re-loading the file from disk"""

        # XXX: currently hardcoded for single object

        # this is a HxWx3 tensor (RGBA or RGB data)
        mask = imageio.imread(self.compositor.fname_masks[0])
        mask = np.sum(mask, axis=2)
        return boundingbox_from_mask(mask)


    def compute_3dbbox(self):
        # TODO: probably, using numpy is not at all required, we could directly
        #       store to lists. have to decide if we want this or not

        # TODO: check if order of vertices is the same as for amira_deep_vision.
        #       At the moment this is probably not the case, and we have to be careful
        #       to translate between OpenCV's coordinate system convention, and
        #       blender's (OpenGL).

        # Blender has the coordinates and bounding box in the following way.
        #
        # The world coordinate system has x pointing right, y pointing forward,
        # z pointing upwards. Then, indexing with x/y/z, the bounding box
        # corners are taken from the following axes:
        #
        #   0:  -x/-y/-z
        #   1:  -x/-y/+z
        #   2:  -x/+y/+z
        #   3:  -x/+y/-z
        #   4:  +x/-y/-z
        #   5:  +x/-y/+z
        #   6:  +x/+y/+z
        #   7:  +x/+y/-z

        # 0. storage for numpy arrays.

        np_aabb = np.zeros((9, 3))
        np_oobb = np.zeros((9, 3))
        np_corners3d = np.zeros((9, 2))

        # 1. get centroid and bounding box of object in world coordiantes by
        # applying the objects rotation matrix to the bounding box of the object

        # axis aligned (no object rotation)
        aabb = [Vector(v) for v in self.cap_obj.bound_box]
        aa_centroid = aabb[0] + (aabb[6] - aabb[0]) / 2.0
        # convert to numpy
        np_aabb[0, :] = np.array((aa_centroid[0], aa_centroid[1], aa_centroid[2]))
        for i in range(8):
            np_aabb[i+1, :] = np.array((aabb[i][0], aabb[i][1], aabb[i][2]))

        # object aligned (that is, including object rotation)
        oobb = [self.cap_obj.matrix_world @ v for v in aabb]
        oo_centroid = oobb[0] + (oobb[6] - oobb[0]) / 2.0
        # convert to numpy
        np_oobb[0, :] = np.array((oo_centroid[0], oo_centroid[1], oo_centroid[2]))
        for i in range(8):
            np_oobb[i+1, :] = np.array((oobb[i][0], oobb[i][1], oobb[i][2]))

        # project centroid+vertices and convert to pixel coordinates
        corners3d = []
        prj = abr_geom.project_p3d(oo_centroid, self.cam)
        pix = abr_geom.p2d_to_pixel_coords(prj)
        corners3d.append(pix)
        np_corners3d[0, :] = np.array((corners3d[-1][0], corners3d[-1][1]))

        for i,v in enumerate(oobb):
            prj = abr_geom.project_p3d(v, self.cam)
            pix = abr_geom.p2d_to_pixel_coords(prj)
            corners3d.append(pix)
            np_corners3d[i+1, :] = np.array((corners3d[-1][0], corners3d[-1][1]))

        return np_aabb, np_oobb, np_corners3d


    def postprocess(self):
        """Postprocessing the scene.

        This step will compute all the data that is relevant for
        PoseRenderResult. This data will then be saved to json. In addition,
        postprocessing will fix the filenames generated by blender.
        """

        # the compositor postprocessing takes care of fixing file names
        self.compositor.postprocess()

        # compute bounding boxes and save annotations
        corners2d = self.compute_2dbbox()
        aabb, oobb, corners3d =  self.compute_3dbbox()
        self.save_annotations(corners2d, corners3d, aabb, oobb)


    def randomize(self):
        """Set an arbitrary location and rotation for the object"""

        ok = False
        while not ok:
            # random R,t
            self.cap_obj.location = Vector((1.0 * np.random.rand(3) - 0.5))
            self.cap_obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            # Test if object is still visible. That is, none of the vertices
            # should lie outside the visible pixel-space
            vs  = [self.cap_obj.matrix_world @ Vector(v) for v in self.cap_obj.bound_box]
            ps  = [abr_geom.project_p3d(v, self.cam) for v in vs]
            pxs = [abr_geom.p2d_to_pixel_coords(p) for p in ps]
            oks = [px[0] >= 0 and px[0] < self.width and px[1] >= 0 and px[1] < self.height for px in pxs]
            ok = all(oks)

