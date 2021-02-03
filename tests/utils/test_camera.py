#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import unittest
import bpy
import numpy as np
import numpy.testing as npt
from amira_blender_rendering.datastructures import DynamicStruct
from amira_blender_rendering.utils import camera
from amira_blender_rendering.utils.io import expandpath
import tests


@tests.register(name='test_utils')
class TestCamera(unittest.TestCase):

    def setUp(self):
        cam_info = DynamicStruct()
        cam_info.intrinsic = None
        cam_info.width = 640
        cam_info.height = 480
        cam_info.sensor_width = 0
        cam_info.focal_length = 0
        cam_info.hfov = 0
        cam_info.intrinsics_conversion_mode = None
        self._cam_info = cam_info

        # load blender test file
        self._testfile = 'test.blend'
        self._testpath = os.path.join(os.getcwd(), 'tests', 'data', self._testfile)

        # load test file (2 objects, 1 camera and 1 light)
        bpy.ops.wm.open_mainfile(filepath=expandpath(self._testpath))

        self._cam = bpy.context.scene.objects['Camera']

    def test_intrinsics_to_numpy(self):
        self._cam_info.intrinsic = '390, 390, 320, 240'
        npt.assert_almost_equal(np.array([390, 390, 320, 240]), camera._intrinsics_to_numpy(self._cam_info),
                                err_msg='Intrisic conversion incorrect')
 
    def test_set_camera_swfl(self):
        "test setting up camera with sensor-width and focal length"
        # overwrite parameters
        self._cam_info.sensor_width = 1.89882275303
        self._cam_info.focal_length = 1.158
        K_test = np.asarray([[1170.91, 0, 960], [0, 1170.91, 540], [0, 0, 1]])
        # set camera and get matrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2, err_msg='Error while setting camera from swfl')

    def test_set_camera_hfov(self):
        "test setting up camera with field of view"
        # overwrite parameters
        self._cam_info.hfov = 78.694
        K_test = np.asarray([[73.2517014, 0, 960], [0, 73.2517014, 540], [0, 0, 1]])
        # set camera and get matrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, err_msg='Error while setting camera from hfov')

    def test_set_camera_intrisics(self):
        # overwrite parameters
        self._cam_info.intrinsic = np.array([390, 390, 320, 240])
        self._cam_info.intrinsics_conversion_mode = 'fov'
        K_test = np.asarray([[2666.67, 0, 960], [0, 2666.67, 540], [0, 0, 1]])
        # set camera and get matrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2,
                                err_msg='Error while setting camera from intrinsics with conv. mode "fov"')

        # overwrite parameters
        self._cam_info.intrinsics_conversion_mode = 'mm'
        K_test = np.asarray([[2666.67, 0, 960], [0, 2666.67, 540], [0, 0, 1]])
        # set camera and get amtrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2,
                                err_msg='Error while setting camera from intrinsics with conv. mode "mm"')

    def test_get_camera_locations(self):
        test_locations = {'Camera': np.array([0, 0, 20])}
        locations = camera.get_current_cameras_locations(['Camera'])
        self.assertEqual(len(test_locations), len(locations), 'Wrong number of Cameras locations')
        self.assertEqual(test_locations.keys(), locations.keys(), 'Wrong camera names')
        npt.assert_almost_equal(test_locations['Camera'], locations['Camera'],
                                err_msg='Wrong camera locations')

    def tearDown(self):
        pass


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCamera))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
