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
from amira_blender_rendering.math import conversions


class TestConversions(unittest.TestCase):

    def setUp(self):
        # given amount of bu.
        self.bu = 1

    def test_from_bu_to_given_unit(self):
        """Convert from b.u. (blender unit) to given real unit. (1 b.u. = 1 m)"""
        self.assertEqual(1 * self.bu, conversions.bu_to_m(self.bu), 'Error while converting bu to m')
        self.assertEqual(100 * self.bu, conversions.bu_to_cm(self.bu), 'Error while converting bu to cm')
        self.assertEqual(1000 * self.bu, conversions.bu_to_mm(self.bu), 'Error while converting bu to mm')

    def tearDown(self):
        pass


# currently this is mandatory for running our tests in blender.
# Each test file should comprise:
#   - (at least) one unittest.TestCase implementing all the desired tests
#   - a main function (see below) to collect all the implemented tests in a suite and run them.
# Currently we cannot rely on the standard "discover" functionality provided by the unittest framework
# since blender python scripting does not allow running python script as modules.
def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConversions))
    runner = unittest.TextTestRunner()
    runner.run(suite)


# making this a callable module is optional but good practice
if __name__ == '__main__':
    main()
