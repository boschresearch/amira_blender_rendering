#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from math import ceil, log
import numpy as np
from skimage import img_as_float, img_as_int

import imageio
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from abr_dataset_tools.utils import expandpath, parse_dataset_configs, \
    build_dataset_info, build_directory_info, build_render_setup, build_camera_info, \
    plot_sample


class ABRDataset:
    """Class to handle dataset generated using AMIRA Blender Rendering"""

    def __init__(self, root, convention: str = 'opencv', **kwargs):
        """
        Class Constructor.

        Args:
            root(str): (absolute) path to dataset root directory

        Optional Args:
            convention(str): annotations convention ['opencv' , 'opengl']. Default: 'opencv'
    
        Kwargs Args:
            transform: torch-like sequential transform to apply to images while loading.
                        Transform must be implemented as a series of callable handling
                        the images in the loaded sample.
        
        Returns:
            None

        Raises:
            FileNotFoundError: given root path does not exists.
            FileNotFoundError: Dataset.cfg file missing in dataset.
            RunTimeError: given root path lead to a dataset not adhering to ABR format.
            ValueError: given convention not supported
        """
        super(ABRDataset, self).__init__()
        self._root = expandpath(root, check_file=True)
        self.transform = kwargs.get('transform', None)  # allow for tranform to be applied
        
        # load configuration from root dir
        dset_cfg = parse_dataset_configs(self._root)

        # Build structures containing info about dataset directory structure, rendering, dataset, etc.
        # Essentially, this extracts the parts from the configuration file
        self.dataset_info = build_dataset_info(dset_cfg['dataset'])
        self.render_setup = build_render_setup(dset_cfg['render_setup'])
        self.dir_info = build_directory_info(self._root)
        self.camera_info = build_camera_info(dset_cfg['camera_info'])

        # additional variable
        self.format_width = int(ceil(log(len(self), 10)))

        # early on check convention
        if convention == 'opencv':
            self.annotations_path = self.dir_info['annotations']['opencv']
        elif convention == 'opengl':
            self.annotations_path = self.dir_info['annotations']['opengl']
        else:
            raise ValueError(f'Uknown convention "{self.cfg.convention}')

        # read parts from scenario setup and store in list self.parts,
        # where the list index corresponds to the model_id
        self.parts = list()
        for id, part in enumerate(dset_cfg['scenario_setup']['target_objects'].split(',')):
            obj_type, _ = part.split(':')
            
            # here we distinguish if we copy a part from the proto objects
            # within a scene, or if we have to load it from file
            is_proto_object = not obj_type.startswith('parts.')
            if not is_proto_object:
                # split off the prefix for all files that we load from blender
                obj_type = obj_type[6:]
        
            part_info = {
                'model_name': obj_type,
                'model_id': id
            }
            if 'parts.ply' in dset_cfg.sections():
                if obj_type in dset_cfg['parts.ply']:
                    part_info['path'] = expandpath(dset_cfg['parts.ply'][obj_type])
            if 'parts.ply_scale' in dset_cfg.sections():
                if obj_type in dset_cfg['parts.ply_scale']:
                    part_info['scale'] = dset_cfg['parts.ply_scale'][obj_type]
            self.parts.append(part_info)

    def load_sample(self, index):
        """
        Load sample from dataset given index number

        Args:
            index(int): index value for image

        Returns:
            sample(dict): dictionary with information regarding images and objects contained therein
        """

        # get the name of the pngs
        fname_png = "{:0{width}d}.png".format(index, width=self.format_width)
        fname_json = "{:0{width}d}.json".format(index, width=self.format_width)

        # load the json file and extract relevant information
        with open(os.path.join(self.annotations_path, fname_json), 'r') as f:
            annotations = json.load(f)

        # init
        sample = dict()

        # fill out sample
        sample['image_id'] = index
        sample['num_objects'] = len(annotations)
        sample['objects'] = list()

        composite_mask = None
        for a in annotations:
            obj = dict()
   
            # set model and object name and id. Support single and multi object annotations
            obj['object_class_name'] = a['model_name']
            obj['object_class_id'] = a['model_id']
            obj['object_name'] = a['object_name']
            obj['object_id'] = a['object_id']
            
            # work out pose: convert to expected format first
            obj['pose'] = {
                'q': np.array(a['pose']['q']),  # WXYZ
                't': np.array(a['pose']['t'])
            }

            # work out boxes
            obj['bboxes'] = {
                'corners2d': np.array(a['bbox']['corners2d']),
                'corners3d': np.array(a['bbox']['corners3d']),
                'aabb': np.array(a['bbox']['aabb']),
                'oobb': np.array(a['bbox']['oobb'])
            }

            fname_mask_png = "{:0{width}d}_{:0{width}d}_{:0{width}d}.png".format(index, obj['model_id'],
                                                                                 obj['object_id'],
                                                                                 width=self.format_width)
            mask = imageio.imread(os.path.join(self.dir_info['images']['mask'], fname_mask_png))
    
            # collapse mask and depth to single axis (blender returns mask and depth with 3 channels)
            mask = (mask[:, :, 0] / np.max(mask)).astype(np.uint8)
            
            obj['mask'] = mask

            # merge composite mask
            if composite_mask is None:
                composite_mask = mask
            else:
                composite_mask[mask != 0] = 1
            
            sample['objects'].append(obj)

        # work out images
        rgb = imageio.imread(os.path.join(self.dir_info['images']['rgb'], fname_png))
        depth = imageio.imread(os.path.join(self.dir_info['images']['depth'], fname_png.replace("png", "exr")))
        # collapse depth to single axis
        depth = depth[:, :, 0]

        # assign images
        sample['images'] = {
            'rgb': img_as_float(rgb).astype(np.float32),
            'mask': img_as_int((composite_mask / np.max(composite_mask)).astype(np.int16)).astype(np.uint8),
            'depth': np.asarray(depth, dtype=np.float32)  # keep depth info
        }
        return sample

    def apply_transform(self, sample):
        if self.transform is not None:
            sample = self.transform(sample)
        return sample

    def get_sample(self, index):
        """
        Public interface to load samples from given index

        Args:
            index(int): index of desired sample
        
        Returns:
            sample(dict): dictionary with sample info (images, objects)

        Raises:
            OverflowError: index is out of dataset bound
        """
        if not 0 <= index < len(self):
            raise OverflowError('Given index outside dataset size')
        return self.__getitem__(index)

    def get_samples(self, indexes):
        """Public interface to load a list of samples from given indexes

        Args:
            indexes(list/iterable): iterable with desired indexes to load
        
        Returns:
            list(dict): list with samples corresponding to given indexes
        
        Raises:
            OverflowError: (at least) one of the index is out of dataset bound
        """
        samples = []
        for i in indexes:
            samples.append(self.get_sample(i))
        return samples

    def get_images(self, index):
        """
        Public interface to load images (rgb, depth, mask) corresponding to given index
        
        Args:
            index(int): index to load
        
        Returns:
            images(dict): dict containing (rgb, depth, mask)
        
        Raises:
            OverflowError: index is out of dataset bound
        """
        return self.get_sample(index)['images']

    def get_rgb(self, index):
        """
        Public interface to load rgb image corresponding to given index
        
        Args:
            index(int): index to load
        
        Returns:
            images(np.array): array with rgb image as a float [0, 1]
        
        Raises:
            OverflowError: index is out of dataset bound
        """
        return self.get_images(index)['rgb']
    
    def get_depth(self, index):
        """
        Public interface to load depth image corresponding to given index
        
        Args:
            index(int): index to load
        
        Returns:
            images(np.array): array with depth image with depth values representing distance in m
        
        Raises:
            OverflowError: index is out of dataset bound
        """
        return self.get_images(index)['depth']

    def get_mask(self, index):
        """
        Public interface to load seg. mask corresponding to given index
        
        Args:
            index(int): index to load
        
        Returns:
            images(np.array): array with seg. mask as a int [0, 255]
        
        Raises:
            OverflowError: index is out of dataset bound
        """
        return self.get_images(index)['mask']

    def plot_images(self, index, plot_2d_box: bool = False, plot_3d_box: bool = False):
        """Public interface to plot images from sample

        Args:
            index(int): index of sample to plot

        Optional Args:
            plot_2d_box(bool): if True plot 2d bounding box for objects. Default: False
            plot_3d_box(bool): if True plot 3d bounding box for objects. Default: False
        """
        plot_sample(self.get_sample(index), target='all', plot_2d_box=plot_2d_box, plot_3d_box=plot_3d_box)

    def plot_rgb(self, index, plot_2d_box: bool = False, plot_3d_box: bool = False):
        """Public interface to plot rgb image from sample

        Args:
            index(int): index of sample to plot

        Optional Args:
            plot_2d_box(bool): if True plot 2d bounding box for objects. Default: False
            plot_3d_box(bool): if True plot 3d bounding box for objects. Default: False
        """
        plot_sample(self.get_sample(index), target='rgb', plot_2d_box=plot_2d_box, plot_3d_box=plot_3d_box)

    def plot_depth(self, index):
        """Public interface to plot depth from sample

        Args:
            index(int): index of sample to plot
        """
        plot_sample(self.get_sample(index), target='depth')

    def plot_mask(self, index):
        """Public interface to plot composite seg. mask from sample

        Args:
            index(int): index of sample to plot
        """
        plot_sample(self.get_sample(index), target='mask')

    def get_parts(self):
        return self.parts
    
    def __len__(self):
        return self.dataset_info['image_count']

    def __getitem__(self, index):
        sample = self.load_sample(index)
        sample = self.apply_transform(sample)
        return sample
    
    def __iter__(self):
        """Iter over all available dataset samples"""
        for i in range(len(self)):
            yield self.get_sample(i)

    # define class properties: path, parts etc
    @property
    def size(self):
        return len(self)
    
    @property
    def root(self):
        return self._root
    
    @property
    def convention(self):
        return self.camera_info['convention']

    # string representations and methods
    def __str__(self):
        # TODO: api
        return """ \
        Class to handle datasets rendered/generated using Amira Blender Rendering (ABR).\n\n \
        The following API is implemented:\n \
        - TODO
        """

    def str_dir_info(self):
        """Return a formatted str with dataset information"""
        return f"""
Dataset containing {self.size} images\n\
Root directory: {self.dir_info['root']}\n\
    └─ Annotations/\n\
    |   └─ OpenCV/\n\
    |   └─ OpenGL/\n\
    └─ Images/\n\
        └─ rgb/\n\
        └─ depth/\n\
        └─ mask/"""

    def print_dir_info(self):
        """Print dataset information"""
        print(self.str_info())

    def str_sample_struct(self):
        """Return a formatted str of sample structure"""
        return f"""
Sample (dict):
    image_id (numeric):             # id for image related to sample
    num_objects (int):              # number of objects
    images (dict):                  # collection of images
        rgb (np.array):             # rgb image (float [0, 1])
        depth (np.array):           # depth values in m
        mask (np.array):            # composite seg. mask (int [0, 255])
    objects (list(dict)):           # objects with their properties. See create_empty_object_sample
        model_name (str):           # name of the object class (e.g. car, person)
        model_id (numeric):         # id of the class
        object_name (str):          # name of object instance (e.g. blue golf, person with a hat)
        object_id (numeric)         # id of the object instance
        pose (dict):                # object pose
            q (np.array):           # quaternion (WXYZ) embedding rotation
            t (np.array):           # array embedding translation vector
        mask (np.array):            # single object seg. mask
        bboxes (dict):              # struct of bounding boxes
            corners2d (np.array):   # 2D bounding box in pixel space
            corners3d (np.array):   # 3D bounding box in pixel space
            aabb (np.array):        # axis aligned bounding box
            oobb (np.array)         # object oriented bounding box"""
    
    def print_sample_struct(self):
        """Print sample structure"""
        print(self.str_sample_struct())

    def str_info(self):
        """Return formatted string with info"""
        return f"""{self.str_dir_info()}\n{self.str_sample_struct()}"""
    
    def print_info(self):
        """Print info formatted string"""
        print(self.str_info())


if __name__ == '__main__':

    import sys

    help_str = f"""
Simple Test Script for ABR Dataset Tools.

Write out some dataset info and plot a bunch of samples images.

Usage: python -m abr_dataset [option] path
Options and arguments:
-h/--help   : print this help and exit
path        : (absolute) path to dataset to test
"""
    # check input
    if not 1 <= len(sys.argv) <= 3:
        print(help_str)
        exit(0)
    
    if sys.argv[1] in ['--help', '-h']:
        print(help_str)
        exit(0)
    elif len(sys.argv) == 2:
        root = sys.argv[1]
    else:
        root = sys.argv[2]
    # try out with given path to root directory
    dset = ABRDataset(root=root, convention='opencv')

    dset.print_info()

    # plot a couple of samples
    for i in range(min(5, len(dset))):
        dset.plot_images(i)
