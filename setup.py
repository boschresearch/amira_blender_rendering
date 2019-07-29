#!/usr/bin/env python
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['amira_blender_robot'],
    package_dir={'': 'src'},
    package_data={'amira_blender_robot': ['assets/*.*']},
)

setup(**d)
