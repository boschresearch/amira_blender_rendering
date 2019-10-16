#!/usr/bin/env python

# blender

import bpy
from mathutils import Vector
import os, time
import numpy as np
from random import randint

from amira_blender_rendering import camera_utils
from amira_blender_rendering import blender_utils as blnd
from amira_blender_rendering.utils import expandpath
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom




class PandaTable(
        abr_scenes.RenderedObjectsBase):
    """Panda Table scene which will get loaded from blend file"""

    def __init__(self, base_filename: str, dirinfo, K, width, height, **kwargs):
        # TODO: change hardcoded settings to configurable arguments
        # TODO: change from inheritance to composition to avoid having
        #       constructor after setting up fields
        self.blend_file_path = expandpath('~/gfx/modeling/robottable_one_object_each.blend')
        self.primary_camera = 'CameraOrbbec'
        self.obj = None

        # parent constructor
        super(PandaTable, self).__init__(base_filename, dirinfo, K, width, height)


    def render(self):
        bpy.context.scene.render.engine = "CYCLES"
        bpy.ops.render.render(write_still=False)

    def setup_scene(self):
        # load scene from file
        bpy.ops.wm.open_mainfile(filepath=self.blend_file_path)

    def setup_camera(self):
        """Setup the primary camera, and set field"""
        # the scene has multiple cameras set up. Make sure that the 'right'
        # camera is used
        scene  = bpy.context.scene
        camera = scene.objects[self.primary_camera]
        scene.camera = camera
        # make sure to set this field
        self.cam = camera


    def setup_lighting(self):
        # Lighting is already set up in blend file
        pass

    def setup_object(self):
        # objects are already loaded in blend file. make sure to have the object
        # also available
        self.obj = bpy.context.scene.objects['ToolCap']

    def setup_environment(self):
        # environment is already set up in blend file
        pass

    def randomize(self):
        # Iterate animation a couple of times
        ok = False

        while not ok:
            # TODO: randomize object location

            # forward compute some frames. number of frames is randomly selected
            n_frames = randint(15, 30)

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            print(f"Forward simulation of {n_frames} frames")
            scene = bpy.context.scene
            for i in range(n_frames):
                scene.frame_set(i+1)

            # test if the object is visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            ok = abr_geom.test_visibility(self.obj, cam, self.width, self.height)

            # XXX: DEBUG, we exit the loop because real randomization is not yet
            # implemented
            break

        # XXX: DEBUG
        if not ok:
            print(f"WARNING: Object not in view frustum")
            time.sleep(2)


