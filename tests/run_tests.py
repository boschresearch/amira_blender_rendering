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

"""This script is used to run all implemented tests.
NOTE: Newly implemented tests must be added below in import_and_run_implemented_tests
"""

import sys
import os
import argparse


def err_msg(name):
    return f"Could not import '{name}'. Install as a pkg, or specify a path with corresponding cmd-line arg."


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def import_abr(path=None, name='amira_blender_rendering'):
    """(Try to) import amira_blender_rendering.

    This function tries to import amira_blender_rendering (abr) either from
    pip-installed packages (if path=None), or from a certain location. This is
    required because, to run rendering, we need to pass a python script to
    blender. This specific script is packaged within abr. After importing, we
    can query abr for its location and go on from there.
    
    Args:
        path (str): None, or path to amira_blender_rendering.
    """
    global abr

    if path is None:
        try:
            import amira_blender_rendering as abr
        except ImportError:
            print(err_msg(name))
            sys.exit(1)
    else:
        abr_path = os.path.expanduser(os.path.expandvars(os.path.join(path, 'src')))
        if not os.path.exists(abr_path):
            print(err_msg(name))
            sys.exit(1)
        sys.path.append(abr_path)
        try:
            import amira_blender_rendering as abr
        except ImportError:
            print(err_msg(name))
            sys.exit(1)


def import_tests(path, name='tests'):
    global abr_tests

    if path is None:
        try:
            import tests as abr_tests
        except ImportError:
            print(err_msg(name))
            sys.exit(1)
    else:
        tests_path = os.path.expanduser(os.path.expandvars(path))
        if not os.path.exists(tests_path):
            print(err_msg(name))
            sys.exit(1)
        sys.path.append(tests_path)
        try:
            import tests as abr_tests
        except ImportError:
            print(err_msg(name))
            sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Run tests for amira_blender_rendering in blender',
                                     prog="blender -b -P " + __file__)
    parser.add_argument('--abr-path', type=str, default=None, dest='abr_path',
                        help='Path to amira_blender_rendering root directory, .e.g, ~/amira_blender_rendering')
    args = parser.parse_args(args=get_argv())
    return args


def main():
    # set up (parse args and import packages)
    args = parse_arguments()
    import_abr(args.abr_path)
    import_tests(args.abr_path)
    # run tests
    import_and_run_implemented_tests()


# new tests should be added here
def import_and_run_implemented_tests():
    # math tests
    from tests.math import test_conversions, test_geometry
    test_conversions.main()
    test_geometry.main()

    # utils tests
    from tests.utils import test_annotation, test_converters, test_camera
    test_annotation.main()
    test_converters.main()
    test_camera.main()


if __name__ == "__main__":
    main()
