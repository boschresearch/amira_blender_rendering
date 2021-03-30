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
from amira_blender_rendering.datastructures import DynamicStruct, Configuration
from amira_blender_rendering.utils import camera
from amira_blender_rendering.utils.io import expandpath
import tests


@tests.register(name='test_utils')
class TestCamera(unittest.TestCase):

    def setUp(self):
        cam_info = DynamicStruct()
        cam_info.intrinsic = None
        cam_info.sensor_width = 0
        cam_info.focal_length = 0
        cam_info.hfov = 0
        cam_info.intrinsics_conversion_mode = None
        self._cam_info = cam_info

        self._width = 640
        self._height = 480

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
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info,
                               width=self._width, height=self._height)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2, err_msg='Error while setting camera from swfl')

    def test_set_camera_hfov(self):
        "test setting up camera with field of view"
        # overwrite parameters
        self._cam_info.hfov = 78.694
        K_test = np.asarray([[73.2517014, 0, 960], [0, 73.2517014, 540], [0, 0, 1]])
        # set camera and get matrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info,
                               width=self._width, height=self._height)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, err_msg='Error while setting camera from hfov')

    def test_set_camera_intrisics(self):
        # overwrite parameters
        self._cam_info.intrinsic = np.array([390, 390, 320, 240])
        self._cam_info.intrinsics_conversion_mode = 'fov'
        K_test = np.asarray([[2666.67, 0, 960], [0, 2666.67, 540], [0, 0, 1]])
        # set camera and get matrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info,
                               width=self._width, height=self._height)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2,
                                err_msg='Error while setting camera from intrinsics with conv. mode "fov"')

        # overwrite parameters
        self._cam_info.intrinsics_conversion_mode = 'mm'
        K_test = np.asarray([[2666.67, 0, 960], [0, 2666.67, 540], [0, 0, 1]])
        # set camera and get amtrix
        camera.set_camera_info(bpy.context.scene, self._cam.data, self._cam_info,
                               width=self._width, height=self._height)
        K = np.asarray(camera.get_calibration_matrix(bpy.context.scene, self._cam.data))
        # test
        npt.assert_almost_equal(K_test, K, decimal=2,
                                err_msg='Error while setting camera from intrinsics with conv. mode "mm"')

    def test_get_camera_location(self):
        test_location = np.array([0, 0, 20])
        location = camera.get_camera_location('Camera')
        npt.assert_almost_equal(test_location, location, err_msg='Wrong camera location')

    def test_get_camera_pose(self):
        test_pose = np.eye(4)
        test_pose[:3, 3] = np.array([0, 0, 20])
        pose = camera.get_camera_pose('Camera')
        npt.assert_almost_equal(test_pose, pose, err_msg='Wrong camera pose')

    def test_generate_multiview_locations(self):
        num_locations = 2
        mode = 'random'
        cfg = Configuration()
        cfg.scale = 0  # because of this the locations are all 0
        locations = camera.generate_multiview_locations(num_locations, mode, config=cfg)
        self.assertEqual(len(locations), num_locations, f'Expected {num_locations} locations, got {len(locations)}')
        npt.assert_almost_equal(np.zeros((3,)), locations[0], err_msg=f'Location should be [0,0,0], got {locations[0]}')

    def test_compute_camera_poses(self):
        # first generate locations
        cfg = Configuration()
        cfg.scale = 0  # because of this the locations are all 0
        locations = camera.generate_multiview_locations(1, 'random', config=cfg)
        # group configuration
        cfg['camera_group'] = camera.CameraGroupConfiguration()
        cfg['camera_group'].aim = 'CameraAim'
        # create aim for the group
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0., 0., 0.), scale=(.1, .1, .1))
        bpy.context.active_object.name = 'CameraAim'
        # # test pose in origin
        test_pose = np.eye(4)
        poses = camera.compute_cameras_poses(['camera_group'], cfg, locations, offset=False)
        npt.assert_almost_equal(np.asarray(poses['Camera'][0]), test_pose, err_msg='Generated pose is incorrect')
        # # shift test pose
        test_pose[:3, 3] = np.array([0, 0, 20])
        poses = camera.compute_cameras_poses(['camera_group'], cfg, locations, offset=True)
        npt.assert_almost_equal(np.asarray(poses['Camera'][0]), test_pose, err_msg='Generated pose is incorrect')

    def tearDown(self):
        pass


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCamera))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
