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


"""Script to implement basic testing functionalities for abr geometry package

NOTE: not all the methods in math.geometry are explicitly tested. Those methods called
within other methods in math.geometry are currently excluded since thery are indirectly tested"""

import os
import unittest
import bpy
import numpy as np
import numpy.testing as npt
from mathutils import Vector, Euler
from amira_blender_rendering.math import geometry
from amira_blender_rendering.utils.io import expandpath


class TestGeometry(unittest.TestCase):

    def setUp(self):
        self._testfile = 'test.blend'
        self._testpath = os.path.join(os.getcwd(), 'tests', 'data', self._testfile)

        # load test file (2 objects, 1 camera and 1 light)
        bpy.ops.wm.open_mainfile(filepath=expandpath(self._testpath))

        # get objects
        self._obj1 = bpy.context.scene.objects['Obj1']
        self._obj2 = bpy.context.scene.objects['Obj2']
        self._obj_non_visible = bpy.context.scene.objects['NonVisibleObj']
        self._cam = bpy.context.scene.objects['Camera']

        self._zeroing = Vector((0, 0, 0))
        self._setup_renderer()

        self._w = 640
        self._h = 480
        bpy.context.scene.render.resolution_x = self._w
        bpy.context.scene.render.resolution_y = self._h

    def test_get_relative_rotation_to_cam_deg(self):
        # compute relative rotation
        rel_rot = geometry.get_relative_rotation_to_cam_deg(self._obj1, self._cam, zeroing=self._zeroing)
        # test
        self.assertEqual(Euler((0, 0, 0)), rel_rot, 'Computed relative rotation incorrect')

    def test_get_relative_transform(self):
        rel_t, rel_R = geometry.get_relative_transform(self._obj1, self._obj2)
        self.assertEqual(Vector((4, 0, 0)), rel_t, 'Relative translation is incorrect')
        self.assertEqual(Euler((0, 0, 0)), rel_R, 'Relative rotation is incorrect')

    def test_test_visibility(self):
        # test of simple visibility tests based on bounding box projection
        self.assertTrue(geometry.test_visibility(self._obj1, self._cam, self._w, self._h),
                        'Visible object appears occluded')
        self.assertFalse(geometry.test_visibility(self._obj_non_visible, self._cam, self._w, self._h),
                         'Non visible object appears visible')
    
    def test_test_occlusion(self):
        # test of ray tracing occlusion test
        scene = bpy.context.scene
        layer = scene.view_layers['View Layer']
        
        # test visibile object
        self.assertFalse(geometry.test_occlusion(scene, layer, self._cam, self._obj1, self._w, self._h, False),
                         'Visible object appears occluded')
        # test non visible object
        self.assertTrue(geometry.test_occlusion(scene, layer, self._cam, self._obj_non_visible, self._w, self._h),
                        'Non visible object appears visible')

    def test_get_world_to_object_transform(self):
        R = np.eye(3)
        c2o_pose = {'R': R, 't': np.array([0, 0, -20])}
        w_pose = geometry.get_world_to_object_transform(c2o_pose, self._cam)

        npt.assert_almost_equal(np.array([0, 0, 0]), w_pose['t'], err_msg='World translation in incorrect')
        npt.assert_almost_equal(np.eye(3), w_pose['R'], err_msg='World rotation is incorrect')
    
    def test_gl2cv(self):
        R_gl = np.eye(3)
        t_gl = np.array([0, 0, -1])
        R_cv_gt = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])
        t_cv_gt = np.array([0, 0, 1])
        R_cv, t_cv = geometry.gl2cv(R_gl, t_gl)

        npt.assert_almost_equal(R_cv_gt, R_cv, err_msg='CV rotation is incorrect')
        npt.assert_almost_equal(t_cv_gt, t_cv, err_msg='CV translation is incorrect')

    def test_rotation_matrix(self):
        alpha = np.pi / 4
        sa = ca = 1. / np.sqrt(2)
        Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
        Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
        Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])

        npt.assert_almost_equal(Rx, geometry.rotation_matrix(alpha, 'x', homogeneous=False),
                                err_msg='Rotation matrix around x is incorrect')
        npt.assert_almost_equal(Ry, geometry.rotation_matrix(alpha, 'y', homogeneous=False),
                                err_msg='Rotation matrix around y is incorrect')
        npt.assert_almost_equal(Rz, geometry.rotation_matrix(alpha, 'z', homogeneous=False),
                                err_msg='Rotation matrix around z is incorrect')

    def test_rotation_matrix_to_quaternion(self):
        R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
        q = 0.5 * np.array([1, 1, 1, 1])
        npt.assert_almost_equal(q, geometry.rotation_matrix_to_quaternion(R))

    def tearDown(self):
        pass

    def _setup_renderer(self):
        # setup hardcoded renderer
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.progressive = 'BRANCHED_PATH'
        bpy.context.scene.cycles.aa_samples = 4


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGeometry))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    unittest.main()
