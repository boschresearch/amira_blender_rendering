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

import argparse
from abr_dataset_tools.abr import ABRDataset

# Test script to run when calling abr_dataset_tools as a module
if __name__ == '__main__':
    
    # parse input
    parser = argparse.ArgumentParser(description='ABR Dataset Tools')
    parser.add_argument('root_path', type=str, help='(Absolute) Path to dataset root directory')
    args = parser.parse_args()
    
    dset = ABRDataset(root=args.root_path, convention='opencv')

    print(dset)

    # plot a couple of samples
    for i in range(min(5, len(dset))):
        dset.plot_images(i)
