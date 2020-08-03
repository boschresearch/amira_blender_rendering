#!/usr/bin/env python3

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

import setuptools


def requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(
    name='abr_dataset_tools',
    packages=['abr_dataset_tools'],
    package_dir={'abr_dataset_tools': 'abr_dataset_tools'},
    version='1.0',
    description='API to handle datasets genereted with AMIRA Blender Rendering',
    long_description=readme(),
    author='AMIRA',
    python_requires='>=3.7.*, <4',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: End Users',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=requirements(),
)
