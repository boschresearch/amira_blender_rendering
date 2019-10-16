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

        # use calibration data?
        if self.K is not None:
            print(f"II: Using camera calibration data")
            self.cam = camera_utils.opencv_to_blender(self.width, self.height, self.K, self.cam)


    def setup_lighting(self):
        # Lighting is already set up in blend file
        pass


    def setup_object(self):
        # objects are already loaded in blend file. make sure to have the object
        # also available
        self.obj = bpy.context.scene.objects['Tool.Cap']


    def setup_environment(self):
        # environment is already set up in blend file
        pass


    def randomize(self):

        # objects of interest + relative plate
        cap   = bpy.context.scene.objects['Tool.Cap']
        cube  = bpy.context.scene.objects['RedCube']
        shaft = bpy.context.scene.objects['DriveShaft']
        plate = bpy.context.scene.objects['RubberPlate']

        # we will set the location relative to the rubber plate. That is,
        # slightly above the plate, and within a volume above the plate that is
        # not too high
        base_location = Vector(plate.location)
        base_location.x = base_location.x + .10 # start a bit more towards the robot
        base_location.y = base_location.y + .10 # start a bit left of the middle (camera is not centered)
        base_location.z = base_location.z + .15 # start 10 cm above the plate
        # range from which to sample random numbers
        range_x = 0.20 # 'depth'
        range_y = 0.30 # 'width'
        range_z = 0.20 # 'height' -> this will lead to objects being at most 5cm close to the plate

        # Iterate animation a couple of times
        ok = False
        while not ok:

            # randomize object location
            for obj in [cap, cube, shaft]:
                obj.location = base_location + Vector(( \
                    (np.random.rand(1) - .5) * range_x, \
                    (np.random.rand(1) - .5) * range_y, \
                    (np.random.rand(1) - .5) * range_z))
                obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            # figure out if objects intersect for debug output
            has_intersections = not (\
                abr_geom.test_intersection(cap, cube) or \
                abr_geom.test_intersection(cap, shaft) or \
                abr_geom.test_intersection(cube, shaft)\
                )

            # DEBUG output
            if has_intersections:
                print(f"WW: object intersections detected")
                time.sleep(2)

            # forward compute some frames. number of frames is randomly selected
            n_frames = randint(1, 20)

            print(f"Forward simulation of {n_frames} frames")
            scene = bpy.context.scene
            for i in range(n_frames):
                scene.frame_set(i+1)

            # test if the object is visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            ok = abr_geom.test_visibility(self.obj, cam, self.width, self.height)

            # DEBUG output, we exit the loop because real randomization is not yet
            if not ok:
                print(f"WW: Target object not in view frustum (location = {self.obj.location})")



class ClutteredPandaTable(
        abr_scenes.RenderedObjectsBase):
    """Panda Table scene which will get loaded from blend file"""

    def __init__(self, base_filename: str, dirinfo, K, width, height, **kwargs):
        # TODO: change hardcoded settings to configurable arguments
        # TODO: change from inheritance to composition to avoid having
        #       constructor after setting up fields
        self.blend_file_path = expandpath('~/gfx/modeling/robottable_cluttered.blend')
        self.primary_camera = 'CameraOrbbec'
        self.obj = None

        # parent constructor
        super(ClutteredPandaTable, self).__init__(base_filename, dirinfo, K, width, height)


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

        # use calibration data?
        if self.K is not None:
            print(f"II: Using camera calibration data")
            self.cam = camera_utils.opencv_to_blender(self.width, self.height, self.K, self.cam)



    def setup_lighting(self):
        # Lighting is already set up in blend file
        pass


    def setup_object(self):
        # objects are already loaded in blend file. make sure to have the object
        # also available
        self.obj = bpy.context.scene.objects['Tool.Cap']


    def setup_environment(self):
        # environment is already set up in blend file
        pass


    def randomize(self):

        # objects of interest + relative plate
        cap    = bpy.context.scene.objects['Tool.Cap']
        plate  = bpy.context.scene.objects['RubberPlate']

        cube_names = [f"RedCube.{d:03}" for d in range(1, 6)]
        cubes  = [bpy.context.scene.objects[s] for s in cube_names]

        shaft_names = [f"DriveShaft.{d:03}" for d in range(12)]
        shafts = [bpy.context.scene.objects[s] for s in shaft_names]

        # we will set the location relative to the rubber plate. That is,
        # slightly above the plate. For this scenario, we will not change the
        # height of the objects!
        base_location = Vector(plate.location)
        base_location.x = base_location.x
        base_location.y = base_location.y

        # range from which to sample random numbers
        range_x = 0.60 # 'depth'
        range_y = 0.90 # 'width'

        # Iterate animation a couple of times
        ok = False
        while not ok:

            # randomize object locations
            for obj in [cap] + cubes + shafts:
                obj.location.x = base_location.x + (np.random.rand(1) - .5) * range_x
                obj.location.y = base_location.y + (np.random.rand(1) - .5) * range_y
                obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            # forward compute some frames. number of frames is randomly selected
            n_frames = randint(1, 40)

            print(f"Forward simulation of {n_frames} frames")
            scene = bpy.context.scene
            for i in range(n_frames):
                scene.frame_set(i+1)

            # test if the object is visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            ok = abr_geom.test_visibility(self.obj, cam, self.width, self.height)

            # DEBUG output, we exit the loop because real randomization is not yet
            if not ok:
                print(f"WW: Target object not in view frustum (location = {self.obj.location})")

