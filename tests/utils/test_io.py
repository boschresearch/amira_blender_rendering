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
import os
from getpass import getuser
from amira_blender_rendering.utils import io


class TestIO(unittest.TestCase):

    def setUp(self):
        self._env_var = 'TESTVAR'
        self._var_value = '~/tmp/testdir'
        self._test_path = os.path.join('/home', getuser(), 'tmp', 'testdir', 'test') 
        os.environ[self._env_var] = self._var_value

    def test_expandpath(self):
        self.assertEqual(self._test_path, io.expandpath('$TESTVAR/test'))
    
    def test_get_my_dir(self):
        self.assertEqual(os.getcwd(), io.get_my_dir('.'))

    def tearDown(self):
        del os.environ[self._env_var]


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIO))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
