#!/usr/bin/env python

# blender
import bpy
from mathutils import Vector, Matrix
import os
import numpy as np

import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom

class SimpleToolCapConfiguration(abr_scenes.BaseConfiguration):
    def __init__(self):
        super(SimpleToolCapConfiguration, self).__init__(name="SimpleToolCap")


class SimpleToolCap():

    """Simple toolcap scene in which we have three point lighting and can set
    some background image.
    """
    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):
        super(SimpleToolCap, self).__init__(base_filename, dirinfo, camerainfo)

        # abr_scenes.RenderedObjectsBase,
        # abr_scenes.ThreePointLighting):




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
        # needs to be re-scaled to fit nicely into blender units. This way, the
        # Toolcap will be about 0.05 blender units high, which corresponds to
        # 0.05m and, thus about 5cm
        self.obj.scale = Vector((0.010, 0.010, 0.010))

    def import_mesh(self):
        """Import the mesh of the cap from a ply file."""
        # load mesh from assets directory
        self.ply_path = os.path.join(blnd.assets_dir, 'tool_cap.ply')
        bpy.ops.import_mesh.ply(filepath=self.ply_path)
        self.obj = bpy.context.object
        self.obj.name = 'Tool.Cap'

    def select_cap(self):
        """Select the cap, which is the object of interest in this scene."""
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(state=True)
        bpy.context.view_layer.objects.active = self.obj

    def setup_material(self):
        """Setup object material"""

        # make sure cap is selected
        self.select_cap()

        # remove any material that's currently assigned to the object and then
        # setup the metal for the cap
        blnd.remove_material_nodes(self.obj)
        blnd.clear_orphaned_materials()

        # add default material and setup nodes (without specifying empty, to get
        # it created automatically)
        self.cap_mat = blnd.add_default_material(self.obj)
        abr_nodes.material_metal_tool_cap.setup_material(self.cap_mat)

    def setup_lighting(self):
        # this scene uses classical three point lighting
        self.setup_three_point_lighting()

    def setup_scene(self):
        """Setup the scene"""
        bpy.context.scene.render.resolution_x = self.camerainfo.width
        bpy.context.scene.render.resolution_y = self.camerainfo.height

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
            self._update_scene()

            # Test if object is still visible. That is, none of the vertices
            # should lie outside the visible pixel-space
            ok = self._test_visibility()

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
        world_pose = abr_geom.get_world_to_object_tranform(pose, self.cam)

        # set pose
        self.obj.location = Vector((world_pose['t']))
        self.obj.rotation_euler = Matrix(world_pose['R']).to_euler()

        # update the scene. unfortunately it doesn't always work to just set
        # the location of the object without recomputing the dependency
        # graph
        self._update_scene()

        # Test if object is still visible. That is, none of the vertices
        # should lie outside the visible pixel-space
        ok = self._test_visibility()
        if not ok:
            raise ValueError('Given pose is lying outside the scene')

    def _update_scene(self):
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()


    def _test_visibility(self):
        vs = [self.obj.matrix_world @ Vector(v) for v in self.obj.bound_box]
        ps = [abr_geom.project_p3d(v, self.cam) for v in vs]
        pxs = [abr_geom.p2d_to_pixel_coords(p) for p in ps]
        oks = [0 <= px[0] < self.camerainfo.width and 0 <= px[1] < self.camerainfo.height for px in pxs]
        return all(oks)

    #
    #
    # TODO: new configurations
    #
    #

    def dump_config(self):
        raise NotImplementedError()

    def generate_dataset(self):
        raise NotImplementedError()

    def generate_viewsphere_dataset(self):
        raise NotImplementedError()

    def teardown():
        raise NotImplementedError()
