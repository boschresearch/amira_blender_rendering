#!/usr/bin/env python

import bpy
from mathutils import Vector
import time
import numpy as np
from random import randint
from math import ceil, log

from amira_blender_rendering import camera_utils
from amira_blender_rendering.utils import expandpath
import amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.math.geometry as abr_geom


class WorkstationScenarios(abr_scenes.RenderedObjectsBase):
    """base class for all workstation scenarios"""

    def __init__(self, base_filename: str, dirinfo, camerainfo, **kwargs):
        super(WorkstationScenarios, self).__init__(base_filename, dirinfo, camerainfo)
        self.config = kwargs.get('config', None)

        # store objects, object types, etc.

    def setup_camera(self):
        """Setup the primary camera, and set field"""
        pass

    def render(self):
        pass

    def setup_scene(self):
        """Load scene from file"""
        pass
