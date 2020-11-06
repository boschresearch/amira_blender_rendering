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
from amira_blender_rendering.utils.io import expandpath
import amira_blender_rendering.scenes.basescenemanager as bsm

"""Test file for main functionalities in amira_blender_rendering.scene.basescenemanager"""


class TestBaseSceneManager(unittest.TestCase):

    def setUp(self):
        self._instance = None
        self._test_texture_path = os.path.join(os.getcwd(), 'tests', 'data', 'test_texture.hdr')

    def test_class(self):
        # test class integrity
        self._instance = bsm.BaseSceneManager()
        self.assertIsInstance(self._instance, bsm.BaseSceneManager)
        
        # this is not an active test but it should rise an error if something is wrong
        self._instance.set_environment_texture(expandpath(self._test_texture_path))

    def tearDown(self):
        del self._instance


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBaseSceneManager))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
