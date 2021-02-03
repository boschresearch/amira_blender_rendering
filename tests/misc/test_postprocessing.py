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
import numpy.testing as npt
import amira_blender_rendering.postprocessing as pp
import tests


"""Test file for main functionalities in amira_blender_rendering.postprocessing"""


@tests.register(name='test_misc')
class TestPostprocessing(unittest.TestCase):

    def setUp(self):
        # mockup mask
        self._mask = np.zeros((10, 10))
        self._mask[:3, :3] = 1
        self._test_box = np.array([[0, 0], [2, 2]])

    def test_bbox_from_mask(self):
        box = pp.boundingbox_from_mask(self._mask)
        npt.assert_array_equal(self._test_box, box, err_msg='Bounding boxes do not match')

    def tearDown(self):
        self._mask = None


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPostprocessing))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
