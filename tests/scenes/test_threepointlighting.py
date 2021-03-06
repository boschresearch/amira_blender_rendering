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
import amira_blender_rendering.scenes.threepointlighting as tpl
import tests

"""Test file for main functionalities in amira_blender_rendering.scene.threepointlighting"""


@tests.register(name='test_scenes')
class TestThreePointLighting(unittest.TestCase):

    def setUp(self):
        self._instance = None

    def test_class(self):
        # test class integrity
        self._instance = tpl.ThreePointLighting()
        self.assertIsInstance(self._instance, tpl.ThreePointLighting)

    def tearDown(self):
        del self._instance


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestThreePointLighting))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
