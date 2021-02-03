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
import argparse
import unittest
from amira_blender_rendering.datastructures import Configuration
import tests


def get_basic_config():
    """
    Define some default basic configuration
    """

    # global configuration
    config = Configuration()
    config.add_param('aint', 1, 'Some int')
    config.add_param('astr', 'a', 'Some string')
    config.add_param('afloat', 10.1, 'Some float')
    config.add_param('alist', ['a', 2, 4.3], 'Some list')
    config.add_param('adict', {'a': 1}, 'Some dict')

    config.add_param('training.network_type', 'dope', 'Network type')
    config.add_param('optimizer.learning_rate', 1.000, 'Learning Rate')
    config.a = '123'

    return config


def get_subconfig(net_type):
    """
    Define configuration for an object. In this case a network names 'retina'
    """
    if not (net_type == 'retina'):
        raise RuntimeError(f"Unsupported network type {net_type}")

    # default retina configuration
    config = Configuration('retina')
    config.add_param('setting', 111, 'some standard setting')
    config.add_param('maybe_alist_of_int', 0, 'some potential list', 'maybe_list')
    config.add_param('empty_list', [], 'some empty list', 'maybe_list')

    # nested configuration for resnet
    config.add_param('resnet', get_resnet_config(), 'resnet help')

    return config


def get_resnet_config():
    """Define config of an additional object. In this case 'resnet'"""
    config = Configuration('resnet')
    config.add_param('foo', True, 'Test variable')
    config.add_param('bar', False, 'Another variable')
    config.add_param('mixed', 555.5, 'Yet another variable')
    config.add_param('maybe_alist_of_float', 1., 'some potential list', 'maybe_list')
    return config


def parse_args(config):

    # parse any arguments specific for the configuration
    config.parse_args()

    # parser for other stuff
    parser = argparse.ArgumentParser(parents=config.get_argparsers(), add_help=False)
    parser.add_argument('-h', '--help', action="store_true", help='show this help message and exit')
    parser.add_argument('-o', '--option', help="some command line option")

    args = parser.parse_args()
    return args


@tests.register(name='test_misc')
class TestConfiguration(unittest.TestCase):

    def setUp(self):
        # path to test config file
        self.config_path = os.path.join(os.getcwd(), 'tests', 'data', 'test.cfg')

        # set up a basic configuration to test
        self.cfg = get_basic_config()

    def test_default_config(self):
        self.assertEqual(self.cfg.aint, 1, 'Expected int 1')
        self.assertEqual(self.cfg.astr, 'a', 'Expected str "a"')
        self.assertEqual(self.cfg.afloat, 10.1, 'Expected float 10.1')
        self.assertEqual(self.cfg.alist, ['a', 2, 4.3], 'Expected list ["a", 2, 4.3]')
        self.assertEqual(self.cfg.adict, {'a': 1}, 'Expected dict {"a":1 }')
        self.assertEqual(self.cfg.a, '123', 'Expected str "123"')
        self.assertEqual(self.cfg.training.network_type, 'dope', 'Default net type should be "dope"')
        self.assertEqual(self.cfg.optimizer.learning_rate, 1.000, 'Expected float 1.000')

    def test_parse_config(self):
        # first parse --> overwrite existing default
        self.cfg.parse_file(self.config_path)

        # test
        self.assertEqual(self.cfg.training.network_type, 'retina', 'Config network type should be "retina"')
        self.assertEqual(self.cfg.optimizer.learning_rate, 0.001, 'Expected float 0.001')
        self.assertEqual(self.cfg.resnet.mixed, '123.4', 'Expected str "123.4"')

        # get subconfig...
        net_type = self.cfg.training.network_type.lower()
        self.cfg[net_type] = get_subconfig(net_type)

        # ...and test subconfig default
        self.assertEqual(self.cfg.retina.maybe_alist_of_int, 0, 'Expected default int 0')
        self.assertTrue(self.cfg.retina.resnet.foo, 'Expected foo to default to True')

        # re-parse...
        self.cfg.parse_file(self.config_path, only_section=net_type)

        # ...and re-test
        self.assertEqual(self.cfg.retina.setting, 123, 'Expected parameter to be set to 123')
        self.assertEqual(self.cfg.retina.maybe_alist_of_int, [1, 1], 'Expected parameter to be set to [1,1]')
        self.assertFalse(self.cfg.retina.resnet.foo, 'Expected foo to be set to False')
        self.assertEqual(self.cfg.retina.resnet.mixed, 321.1, 'Expected parameter to be set to 321.1')
        self.assertEqual(self.cfg.retina.resnet.maybe_alist_of_float, [1.1, 1.2],
                         'Expected parameter to be set to [1.1, 1.2]')

    def tearDown(self):
        del self.cfg


def main():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConfiguration))
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
