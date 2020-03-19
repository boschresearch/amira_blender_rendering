#!/usr/bin/env python

# blender

import bpy
from mathutils import Vector
import time
import numpy as np
from random import randint
from math import ceil, log

import amira_blender_rendering.utils.camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom


class BasePandaTable(abr_scenes.RenderedObjectsBase):
    """Common functions for all panda table scenes"""

    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):
        super(BasePandaTable, self).__init__(base_filename, dirinfo, camerainfo)

    def setup_camera(self):
        """Setup the primary camera, and set field"""
        # the scene has multiple cameras set up. Make sure that the 'right'
        # camera is used
        scene = bpy.context.scene
        camera = scene.objects[self.primary_camera]
        scene.camera = camera

        # make sure to set this field
        self.cam = camera

        # use calibration data?
        if self.camerainfo.K is not None:
            print(f"II: Using camera calibration data")
            self.cam = camera_utils.opencv_to_blender(self.camerainfo.K, self.cam)

        # re-set camera and set rendering size
        bpy.context.scene.camera = self.cam
        bpy.context.scene.render.resolution_x = self.camerainfo.width
        bpy.context.scene.render.resolution_y = self.camerainfo.height

    def render(self):
        bpy.context.scene.render.engine = "CYCLES"
        bpy.ops.render.render(write_still=False)

    def setup_scene(self):
        # load scene from file
        bpy.ops.wm.open_mainfile(filepath=self.blend_file_path)

    def setup_lighting(self):
        # Lighting is already set up in blend file
        pass

    def setup_objects(self):
        # objects are already loaded in blend file. make sure to have the object
        # also available
        self.objs = [{
            'id_mask': '',
            'model_name': self.obj_name,
            'model_id': None,
            'object_id': None,
            'bpy': bpy.context.scene.objects[self.obj_name]
        }]

    def setup_environment(self):
        # environment is already set up in blend file
        pass

    def reset(self):
        """Reset the panda table scene"""

        # set to first frame in animation. Leaving the scene at another frame
        # leads to a blender segfault
        bpy.context.scene.frame_set(1)
        return self


"""
 SINGLE OBJECT SCENES
"""


class PandaTable(BasePandaTable):
    """Panda Table scene which will get loaded from blend file"""

    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):
        # TODO: change from inheritance to composition to avoid having
        #       constructor after setting up fields

        self.config = kwargs.get('config', None)
        self.blend_file_path = expandpath(
            self.config['blend_file'] if self.config is not None else '~/gfx/modeling/robottable_one_object_each.blend')
        self.primary_camera = 'CameraOrbbec'
        self.objs = None
        self.obj_name = self.config['target_objects'] if self.config is not None else 'Tool.Cap'

        # parent constructor
        super(PandaTable, self).__init__(base_filename, dirinfo, camerainfo, **kwargs)

    def randomize(self):
        # objects of interest + relative plate
        cap = bpy.context.scene.objects['Tool.Cap']
        cube = bpy.context.scene.objects['RedCube']
        shaft = bpy.context.scene.objects['DriveShaft']
        letterb = None if 'LetterB' not in bpy.context.scene.objects else bpy.context.scene.objects['LetterB']
        plate = bpy.context.scene.objects['RubberPlate']

        # we will set the location relative to the rubber plate. That is,
        # slightly above the plate, and within a volume above the plate that is
        # not too high
        base_location = Vector(plate.location)
        base_location.x = base_location.x + .10  # start a bit more towards the robot
        base_location.y = base_location.y + .10  # start a bit left of the middle (camera is not centered)
        base_location.z = base_location.z + .15  # start 10 cm above the plate
        # range from which to sample random numbers
        range_x = 0.20  # 'depth'
        range_y = 0.30  # 'width'
        range_z = 0.20  # 'height' -> this will lead to objects being at most 5cm close to the plate

        # Iterate animation a couple of times
        ok = False
        while not ok:

            # randomize object location
            for obj in [cap, cube, shaft, letterb]:
                if obj is None:
                    continue

                obj.location = base_location + Vector((
                    (np.random.rand(1) - .5) * range_x,
                    (np.random.rand(1) - .5) * range_y,
                    (np.random.rand(1) - .5) * range_z))
                obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # update the scene. unfortunately it doesn't always work to just set
            # the location of the object without recomputing the dependency
            # graph
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()

            # figure out if objects intersect for debug output
            has_intersections = not (
                abr_geom.test_intersection(cap, cube) or
                abr_geom.test_intersection(cap, shaft) or
                abr_geom.test_intersection(cube, shaft)
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
                scene.frame_set(i + 1)

            # test if the object is visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            ok = abr_geom.test_visibility(self.objs[0]['bpy'], cam, self.camerainfo.width, self.camerainfo.height)

            # DEBUG output, we exit the loop because real randomization is not yet
            if not ok:
                print(f"WW: Target object not in view frustum (location = {self.obj.location})")


class ClutteredPandaTable(BasePandaTable):
    """Cluttered Panda Table scene which will get loaded from blend file"""

    # def __init__(self, base_filename: str, dirinfo, K, width, height, **kwargs):
    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):
        # TODO: change from inheritance to composition to avoid having
        #       constructor after setting up fields
        self.config = kwargs.get('config', None)
        self.blend_file_path = expandpath(
            self.config['blend_file'] if self.config is not None else '~/gfx/modeling/robottable_cluttered.blend')
        self.primary_camera = 'CameraOrbbec'
        self.objs = None
        self.obj_name = self.config['target_objects'] if self.config is not None else 'Tool.Cap'

        # parent constructor
        # super(ClutteredPandaTable, self).__init__(base_filename, dirinfo, K, width, height)
        super(ClutteredPandaTable, self).__init__(base_filename, dirinfo, camerainfo)

    def randomize(self):

        # objects of interest + relative plate
        cap = bpy.context.scene.objects['Tool.Cap']
        plate = bpy.context.scene.objects['RubberPlate']
        letterb = None if 'LetterB' not in bpy.context.scene.objects else bpy.context.scene.objects['LetterB']

        cube_names = [f"RedCube.{d:03}" for d in range(1, 6)]
        cubes = [bpy.context.scene.objects[s] for s in cube_names]

        shaft_names = [f"DriveShaft.{d:03}" for d in range(12)]
        shafts = [bpy.context.scene.objects[s] for s in shaft_names]

        # we will set the location relative to the rubber plate. That is,
        # slightly above the plate. For this scenario, we will not change the
        # height of the objects!
        base_location = Vector(plate.location)
        base_location.x = base_location.x
        base_location.y = base_location.y

        # range from which to sample random numbers
        range_x = 0.60  # 'depth'
        range_y = 0.90  # 'width'

        # Iterate animation a couple of times
        ok = False
        while not ok:

            # randomize object locations
            for obj in [cap, letterb] + cubes + shafts:
                if obj is None:
                    continue

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
                scene.frame_set(i + 1)

            # test if the object is visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            ok = abr_geom.test_visibility(self.objs[0]['bpy'], cam, self.camerainfo.width, self.camerainfo.height)
            if not ok:
                print(f"II: Target object not in view frustum (location = {self.objs[0]['bpy'].location})")


"""
 SINGLE OBJECT SCENES
"""


class MultiObjectsClutteredPandaTable(BasePandaTable):
    """Cluttered Panda Table scene which will get loaded from blend file"""

    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):

        self.config = kwargs.get('config', None)
        self.blend_file_path = expandpath(
            self.config['blend_file'] if self.config is not None else '~/gfx/modeling/robottable_cluttered.blend')
        self.primary_camera = 'CameraOrbbec'
        self.objs = list()
        self.objs_types = self.config['target_objects']
        self.nontarget_objs = list()
        self.nontarget_objs_types = ['RedCube', 'DriveShaft']

        # parent constructor
        super(MultiObjectsClutteredPandaTable, self).__init__(base_filename, dirinfo, camerainfo, **kwargs)

        # collect all non controlled movable objects
        self.setup_objects(objs=self.nontarget_objs, objs_types=self.nontarget_objs_types)

    def setup_objects(self, objs=None, objs_types=None):
        # objects are already loaded in blend file. make sure to have all the target
        # objects also available.
        if objs is None:
            objs = self.objs
        if objs_types is None:
            objs_types = self.objs_types

        objs_counts = [0 for _ in range(len(objs_types))]
        for i, obj_type in enumerate(objs_types):
            # fill up object instances
            for bpy_obj in bpy.context.scene.objects:
                if obj_type in bpy_obj.name:
                    objs.append({
                        'id_mask': '',
                        'model_name': obj_type,
                        'model_id': i,
                        'object_id': objs_counts[i],
                        'bpy': bpy_obj
                    })
                    objs_counts[i] += 1

        # TODO: how can this work? line 300 uses i, which is not defined in this
        # scope
        # build masks id for compositor
        m_w = ceil(log(len(objs_types)))  # format width for number of model types
        o_w = ceil(log(objs_counts[i]))  # format width for number of objects of same model
        for i, obj in enumerate(objs):
            id_mask = f"_{obj['model_id']:0{m_w}}_{obj['object_id']:0{o_w}}"
            obj['id_mask'] = id_mask

    def randomize(self):

        # objects of interest + relative plate
        plate = bpy.context.scene.objects['RubberPlate']

        # we will set the location relative to the rubber plate. That is,
        # slightly above the plate. For this scenario, we will not change the
        # height of the objects!
        base_location = Vector(plate.location)
        base_location.x = base_location.x
        base_location.y = base_location.y

        # range from which to sample random numbers
        range_x = 0.60
        range_y = 0.90

        # Iterate animation a couple of times
        ok = False
        while not ok:

            # randomize movable object locations
            for obj in self.objs + self.nontarget_objs:
                if obj['bpy'] is None:
                    continue
                obj['bpy'].location.x = base_location.x + (np.random.rand(1) - .5) * range_x
                obj['bpy'].location.y = base_location.y + (np.random.rand(1) - .5) * range_y
                obj['bpy'].rotation_euler = Vector((np.random.rand(3) * np.pi))

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
                scene.frame_set(i + 1)

            # test if the objects are visible in the camera scene
            cam = bpy.context.scene.objects[self.primary_camera]
            for obj in self.objs:
                # if any object does not pass the test, set to False and break
                if not abr_geom.test_visibility(obj['bpy'], cam, self.camerainfo.width, self.camerainfo.height):
                    ok = False
                    print(f"II: Object {obj['bpy'].name} not in view frustum (location = {obj['bpy'].location})")
                    break
                # otherwise visibility is ok
                ok = True
