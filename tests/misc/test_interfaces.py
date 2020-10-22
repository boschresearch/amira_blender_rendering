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

import unittest
import numpy as np
import amira_blender_rendering.interfaces as interfaces

"""Test file for main functionalities in amira_blender_rendering.interfaces"""


def _build_render_result():
    result = interfaces.PoseRenderResult(
        object_class_name='test',
        object_class_id=0,
        object_name='test',
        object_id=0,
        rgb_const=None,
        rgb_random=None,
        depth=None,
        mask=None,
        rotation=np.eye(3),  # internally converted to unit quaternion
        translation=np.array([0]),
        corners2d=np.array([0]),
        corners3d=np.array([0]),
        aabb=np.array([0]),
        oobb=np.array([0]),
        dense_features=None,
        mask_name='',
        visible=False,
        camera_rotation=np.eye(3),
        camera_translation=np.array([0]))
    return result


class TestInterfaces(unittest.TestCase):

    def setUp(self):
        # PoseRenderResult mockup data
        self.render_test_data = {
            'object_class_name': 'test',
            'object_class_id': 0,
            'object_name': 'test',
            'object_id': 0,
            'mask_name': '',
            'visible': False,
            'pose': {
                'q': [1, 0, 0, 0],
                't': [0]
            },
            'bbox': {
                'corners2d': [0],
                'corners3d': [0],
                'aabb': [0],
                'oobb': [0]
            },
            'camera_pose': {
                'q': [1, 0, 0, 0],
                't': [0]
            }
        }

    def test_result_collection(self):
        results = interfaces.ResultsCollection()
        r1 = _build_render_result()
        r2 = _build_render_result()

        # test single insertion
        results.add_result(r1)  # current results: [r1]
        self.assertEqual(results.get_result(0), r1)

        # test state dictionary and filtering
        self.assertListEqual(results.state_dict(retain_keys=['object_class_name']), [{'object_class_name': 'test'}])

        # test list insertion
        results.add_results([r2, r1])  # current results: [r1, r2, r1]
        self.assertEqual(results.get_results(), [r1, r2, r1])

        # test lenght
        self.assertEqual(len(results), 3)

    def test_render_result(self):
        result = _build_render_result()
        self.assertDictEqual(result.state_dict(), self.render_test_data)


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestInterfaces))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
