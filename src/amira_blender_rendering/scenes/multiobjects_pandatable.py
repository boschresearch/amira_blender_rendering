#!/usr/bin/env python

# blender

import bpy
from mathutils import Vector
import numpy as np
from random import randint

from amira_blender_rendering import camera_utils
# from amira_blender_rendering import blender_utils as blnd
from amira_blender_rendering.utils import expandpath
# import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom


class MultiObjectsBasePandaTable(abr_scenes.MultiRenderedObjectsBase):
    """Common functions for all panda table scenes"""

    def __init__(self, base_filename: str, dirinfo, K, width, height, **kwargs):
        super(MultiObjectsBasePandaTable, self).__init__(base_filename, dirinfo, K, width, height)

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
        if self.K is not None:
            print(f"II: Using camera calibration data")
            self.cam = camera_utils.opencv_to_blender(self.K, self.cam)

        # re-set camera and set rendering size
        bpy.context.scene.camera = self.cam
        bpy.context.scene.render.resolution_x = self.width
        bpy.context.scene.render.resolution_y = self.height

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
        # objects are already loaded in blend file. make sure to have all the target
        # objects also available.
        for i, obj_type in enumerate(self.objs_types):
            # creation of container for obj_type
            self.objs[obj_type] = {
                'id': i,
                'instance_count': 0,
                'instances': []
            }
            # fill up object instances
            for bpy_obj in bpy.context.scene.objects:
                if obj_type in bpy_obj.name:
                    # create obj instance
                    instance = {
                        'id': self.objs[obj_type]['instance_count'],
                        'name': bpy_obj.name,
                        'obj': bpy_obj
                    }
                    # fill data structure
                    self.objs[obj_type]['instances'].append(instance)
                    self.objs[obj_type]['instance_count'] += 1
                    
    def setup_environment(self):
        # environment is already set up in blend file
        pass

    def reset(self):
        """Reset the panda table scene"""

        # set to first frame in animation. Leaving the scene at another frame
        # leads to a blender segfault
        bpy.context.scene.frame_set(1)
        return self


class MultiObjectsClutteredPandaTable(MultiObjectsBasePandaTable):
    """Cluttered Panda Table scene which will get loaded from blend file"""

    def __init__(self, base_filename: str, dirinfo, K, width, height, **kwargs):
        # TODO: change from inheritance to composition to avoid having
        #       constructor after setting up fields
        # TODO: use Configuration from aps
        # TODO: change signature: filename, basepath, camera_info, kwargs(render_info)
        # NOTE: dirinfo can be build from basepath, h,w,K,camera_type in camera_info
        # NOTE: if we are going to extend this to stereo we definitely need to change
        # signature and send configs, e.g., with right and left camera
        self.config = kwargs.get('config', None)
        self.blend_file_path = self.config['render_setup']['blend_file'] if self.config is not None else '~/gfx/modeling/robottable_cluttered.blend'
        self.blend_file_path = expandpath(self.blend_file_path)
        self.primary_camera = 'CameraOrbbec'
        self.objs = dict()
        
        # TODO: when available, use Configuration parameter of type list
        objs_types_str = self.config['render_setup']['target_objects'] if self.config is not None else 'Tool.Cap'
        self.objs_types = [t for t in objs_types_str.replace(' ', '').split(',') if not t == '']

        # parent constructor
        super(MultiObjectsClutteredPandaTable, self).__init__(base_filename, dirinfo, K, width, height)

    def randomize(self):

        # objects of interest + relative plate
        # cap = bpy.context.scene.objects['Tool.Cap']
        plate = bpy.context.scene.objects['RubberPlate']
        # letterb = None if 'LetterB' not in bpy.context.scene.objects else bpy.context.scene.objects['LetterB']

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

            # randomize uncontrolled object locations
            # TODO: can we unify handling of all objects as in pandatable.ClutteredPandaTable ??
            for obj in cubes + shafts:
                if obj is None:
                    continue
                obj.location.x = base_location.x + (np.random.rand(1) - .5) * range_x
                obj.location.y = base_location.y + (np.random.rand(1) - .5) * range_y
                obj.rotation_euler = Vector((np.random.rand(3) * np.pi))

            # randomize controlled object locations
            for obj_type, obj in self.objs.items():
                for instance in obj['instances']:
                    if instance['obj'] is None:
                        continue
                    instance['obj'].location.x = base_location.x + (np.random.rand(1) - .5) * range_x
                    instance['obj'].location.y = base_location.y + (np.random.rand(1) - .5) * range_y
                    instance['obj'].rotation_euler = Vector((np.random.rand(3) * np.pi))

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
            for obj_type, obj in self.objs.items():
                for instance in obj['instances']:
                    # if any object does not pass the test, set to False and break
                    if not abr_geom.test_visibility(instance['obj'], cam, self.width, self.height):
                        ok = False
                        print(f"II: Object '{obj_type}' (instance {instance['id']}) \
                            not in view frustum (location = {instance['obj'].location})")
                        break
                    # otherwise visibility is ok
                    ok = True
