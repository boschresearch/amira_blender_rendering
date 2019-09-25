#!/usr/bin/env python

# blender
import bpy
from mathutils import Vector
import os
import numpy as np

from amira_blender_rendering import camera_utils
from amira_blender_rendering import blender_utils as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom


class SimpleLetterB(
        abr_scenes.RenderedObjectsBase,
        abr_scenes.ThreePointLighting):
    """Simple letter B scene in which we have three point lighting and can set
    some background image.
    """

    def __init__(self, base_filename: str, dirinfo, K, width, height):
        super(SimpleLetterB, self).__init__(base_filename, dirinfo, K, width, height)

    def setup_object(self):
        # the order of what's done is important. first import and setup the
        # object and its material, then rescale it. otherwise, values from
        # shader nodes might not reflect the correct sizes
        self.import_mesh()
        self.setup_material()
        self.rescale_objects()


    def rescale_objects(self):
        # needs to be re-scaled to fit nicely into blender units
        # the B ply file contains an object description that is suitable for 3D
        # printing. This means that we have to drastically scale the object down
        self.obj.scale = Vector((0.001, 0.001, 0.001))


    def import_mesh(self):
        """Import the mesh of the B from a ply file."""
        # load mesh from assets directory
        self.ply_path = os.path.join(blnd.assets_dir, 'B.ply')
        bpy.ops.import_mesh.ply(filepath=self.ply_path)
        self.obj = bpy.context.object
        self.obj.name = 'LetterB'


    def select_B(self):
        """Select the B, which is the object of interest in this scene."""
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(state=True)
        bpy.context.view_layer.objects.active = self.obj


    def setup_material(self):
        """Setup object material"""

        # make sure B is selected
        self.select_B()

        # remove any material that's currently assigned to the object and then
        # setup the metal for the B
        blnd.remove_material_nodes(self.obj)
        blnd.clear_orphaned_materials()

        # add default material and setup nodes (without specifying empty, to get
        # it created automatically)
        self.B_mat = blnd.add_default_material(self.obj)
        abr_nodes.material_3Dprinted_plastic.setup_material(self.B_mat)


    def setup_lighting(self):
        # this scene uses classical three point lighting
        self.setup_three_point_lighting()


    def setup_scene(self):
        """Setup the scene"""
        bpy.context.scene.render.resolution_x = self.width
        bpy.context.scene.render.resolution_y = self.height


    def setup_environment(self):
        # This simple scene does not have a specific environment which needs to
        # be set up, such as a table or robot or else.
        pass


    def render(self):
        # Rendering will automatically save images due to the compositor node
        # setup. passing write_still=False prevents writing another file
        bpy.context.scene.render.engine = "CYCLES"
        bpy.ops.render.render(write_still=False)


    def randomize(self):
        """Set an arbitrary location and rotation for the object"""

        ok = False
        while not ok:
            # random R,t
            self.obj.location = Vector((1.0 * np.random.rand(3) - 0.5))
            self.obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            # Test if object is still visible. That is, none of the vertices
            # should lie outside the visible pixel-space
            vs  = [self.obj.matrix_world @ Vector(v) for v in self.obj.bound_box]
            ps  = [abr_geom.project_p3d(v, self.cam) for v in vs]
            pxs = [abr_geom.p2d_to_pixel_coords(p) for p in ps]
            oks = [px[0] >= 0 and px[0] < self.width and px[1] >= 0 and px[1] < self.height for px in pxs]
            ok = all(oks)

