#!/usr/bin/env python3

import os
import shutil
import setuptools

__this_dir = os.path.dirname(__file__)

# Specify version information from file
def get_version():
    with open(os.path.join(__this_dir, 'VERSION')) as version_file:
        return version_file.read().strip()

VERSION = get_version()
PKGNAME = 'amira_blender_rendering'

# Generate the version file
def write_version_file():
    # try to be compatible with
    file_content = """__version__ = '%s'\n""" % (VERSION)
    path = os.path.join(__this_dir, 'src', PKGNAME, 'version.py')
    with open(path, 'w') as f:
        f.write(file_content)

write_version_file()

def requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()

def readme():
    with open('README.md') as f:
        return f.read()

setuptools.setup(
    name='AMIRA Blender Rendering',
    packages=['amira_blender_rendering'],
    package_dir={'':'src'},
    version=VERSION,
    description='AMIRA Blender Rendering Pipeline for Dataset Generation',
    long_description=readme(),
    author='AMIRA',
    python_requires='>=3.7.*, <4',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=requirements(),
    scripts=['scripts/phirm'],
    # Last two arguments will print a warning in catkin, but are required for
    # tox and installation via pip/setup.py
    include_package_data=True,
    zip_safe=True,
)
