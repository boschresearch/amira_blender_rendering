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
from amira_blender_rendering.utils import annotation
import tests


@tests.register(name='test_utils')
class TestAnnotation(unittest.TestCase):

    def setUp(self):
        self._obk = annotation.ObjectBookkeeper()

    def test_object_book_keeper(self):
        self._obk.add('test_class')
        self._obk.add('test_class')
        test_dict = {'id': 0, 'instances': 2}
        none_dict = {'id': None, 'instances': None}
        self._obk.add('another_class')
        self.assertEqual(2, len(self._obk), 'Wrong number of objects classes bookkept')
        self.assertEqual(test_dict, self._obk['test_class'], 'Wrong number of instances bookept')
        self.assertEqual(none_dict, self._obk['none'], 'Unknown class seems to be bookkept')

    def tearDown(self):
        pass


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAnnotation))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
