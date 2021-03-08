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
import shutil
import unittest
import xml.etree.ElementTree as ET
from amira_blender_rendering.utils import converters
from amira_blender_rendering.utils.io import expandpath
import tests


def are_xml_element_equal(e1, e2):
    "test for equality of two given xml elements"
    if len(e1) != len(e2):
        return False
    if e1.tag != e2.tag:
        return False
    if expandpath(e1.text) != expandpath(e2.text):
        return False
    if e1.tail != e2.tail:
        return False
    if e1.attrib != e2.attrib:
        return False
    return True


@tests.register(name='test_utils')
class TestConverters(unittest.TestCase):

    def setUp(self):
        self.environ_cwd = os.environ.get('CWD', None)
        os.environ['CWD'] = os.getcwd()
        self._fname_json = 'test.json'
        self._fname_xml = 'test.xml'
        self._datadir = os.path.join(os.getcwd(), 'tests', 'data')
        self._fpath_json = os.path.join(self._datadir, 'annotations', self._fname_json)
        self._fpath_xml = os.path.join(self._datadir, 'annotations', self._fname_xml)

    def test_to_pascal_voc(self):
        # grab a test annotation and dump to xml
        converters.to_PASCAL_VOC(self._fpath_json)
        # load and compare generated xml
        test_xml = ET.parse(self._fpath_xml)
        converted_xml = ET.parse(os.path.join(self._datadir, 'xml', 'test.xml'))
        for t_xml, c_xml in zip(test_xml.iter(), converted_xml.iter()):
            self.assertTrue(are_xml_element_equal(t_xml, c_xml), 'Different xml element detected')

    def tearDown(self):
        # cleaning directory tree
        shutil.rmtree(os.path.join(self._datadir, 'xml'))
        os.environ.pop('CWD')
        if self.environ_cwd is not None:
            os.environ['CWD'] = self.environ_cwd


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConverters))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
