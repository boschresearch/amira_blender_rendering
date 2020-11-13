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
from configparser import ConfigParser
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as ptc
from abr_dataset_tools import get_logger

logger = get_logger()


def expandpath(path: str, check_file: bool = False):
    """Expand user and other variables in a path
    
    Args:
        path(str): path to expand

    Optional Args:
        check_file(bool): check whether given path corresponds to existing file/directory
    Return
        str: expanded path

    Raises:
        FileNotFoundError: if check_file is True, give path does not exists
        TypeError: given path is not of type str
    """
    if isinstance(path, str):
        path = os.path.expanduser(os.path.expandvars(path))
        if check_file is False or os.path.exists(path):
            return path
        else:
            raise FileNotFoundError(f'Path {path} does not exist - are all environment variables set?')
    else:
        raise TypeError(f'Given path {path} not of type str')


def parse_dataset_configs(root: str):
    """
    Parse dataset configuration file

    Args:
        root(str): (absolute, expanded) path to dataset root directory
    
    Returns:
        ConfigParser
    
    Raises:
        FileNotFoundError: configuration file does not exists
    """
    cfg_path = os.path.join(root, 'Dataset.cfg')
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Dataset configuration file {cfg_path} is missing / does not exists")
    cfg = ConfigParser()
    cfg.read(cfg_path)
    return cfg


def build_render_setup(cfg):
    """Build information struct about the rendering backup from a configuration.

    This performs type conversion to the expected types. Paths contained in
    cfg are expected to be alread expanded. That is, it should not contain
    global variables or other system dependent abbreviations.

    Args:
        cfg (dict): dictionary with Dataset configuration
    
    Returns:
        dict
    
    Raises:
        None
    """
    render_setup = dict()
    render_setup['backend'] = str(cfg['backend'])
    if render_setup['backend'] == 'blender-cycles':
        render_setup['samples'] = float(cfg['samples'])
        render_setup['integrator'] = str(cfg['integrator'])
        render_setup['denoising'] = bool(cfg['denoising'])
        try:
            render_setup['allow_occlusions'] = bool(cfg['allow_occlusions'])
            render_setup['motion_blur'] = bool(cfg['motion_blur'])
        except KeyError:
            render_setup['allow_occlusions'] = ''
            logger.warn('Dataset does not contain occlusions/blur info. It might be an old dataset version.')
    else:
        logger.warn('Loading dataset which have not been rendered with ABR')
    
    return render_setup


def build_dataset_info(cfg):
    """Build information struct about the dataset from a configuration.

    This performs type conversion to the expected types. Paths contained in
    cfg are expected to be alread expanded. That is, it should not contain
    global variables or other system dependent abbreviations.

    Args:
        cfg (dict): Dictionary with Dataset configuration
    
    Returns:
        dict

    Raises:
        None
    """
    dataset_info = dict()
    dataset_info['image_count'] = int(cfg['image_count'])
    dataset_info['scene_type'] = str(cfg['scene_type'])
    dataset_info['base_path'] = str(cfg['base_path'])

    try:
        dataset_info['view_count'] = int(cfg['view_count'])
        dataset_info['scene_count'] = int(cfg['scene_count'])
    except KeyError:
        logger.warn(f'Dataset.cfg in {dataset_info["base_path"]} does not contain some [dataset] keys.'
                    'It might be an old version dataset!')

    return dataset_info


def build_directory_info(root: str):
    """Build a struct with the directory configuration of the dataset.

    The root should be expanded and not contain global variables or
    other system dependent abbreviations.

    Args:
        root (str): (absolute, expanded) path to the root directory of the dataset
        
    Returns:
        dict

    Raises:
        None
    """

    # setup all path related information
    dir_info = {
        'root': root,
        'annotations': {
            'opengl': os.path.join(root, 'Annotations', 'OpenGL'),
            'opencv': os.path.join(root, 'Annotations', 'OpenCV')
        },
        'images': {
            'rgb': os.path.join(root, 'Images', 'rgb'),
            'range': os.path.join(root, 'Images', 'range'),
            'depth': os.path.join(root, 'Images', 'depth'),
            'mask': os.path.join(root, 'Images', 'mask'),
            'backdrop': os.path.join(root, 'Images', 'backdrop')
        }
    }

    return dir_info


def build_camera_info(cfg):
    """Build camera information from parsed configuration

    Args:
        cfg(configParser section): camera configuration

    Returns:
        dict with camera info

    Raises:
        None
    """
    cam_info = {
        'name': str(cfg.get('name', 'Pinhole Camera')),
        'model': str(cfg.get('model', 'pinhole')),
        'uid': str(cfg.get('uid', '')),
        'width': cfg.getfloat('width'),
        'height': cfg.getfloat('height'),
        'zeroing': np.fromstring(cfg.get('zeroing', '0, 0, 0'), sep=',', dtype=np.float32),
        'intrinsic': np.fromstring(cfg.get('instrinsic', '0, 0, 0, 0'), sep=',', dtype=np.float32),
        'sensor_width': float(cfg.get('sensor_width', 0.0)),
        'focal_length': float(cfg.get('focal_lenght', 0.0)),
        'hfov': float(cfg.get('hfov', 0.0)),
        'intrinsics_conversion_mode': str(cfg.get('intrinsics_conversion_mode', '')),
        'original_intrinsic': np.fromstring(cfg.get('original_instrinsic', '0, 0, 0, 0'), sep=',', dtype=np.float32),
    }
    # additional info can be computed by the user
    return cam_info


def quaternion_to_rotation_matrix(q, quat_conv='WXYZ'):
    """
    Computes rotation matrix out of the quaternion (WXYZ (default) or XYZW convention).
    Inverse funtion of rotation_matrix_to_quaternion

    Args:
        q(np.array (4,)): the quaternion (either WXYZ (default) or XYZW convention)
        quat_conv(str): convetion for given quaterion. Defautl: WXYZ

    Returns:
        np.array of shape (3, 3)
    
    Raises:
        RuntimeError: unsupported given convention
    """
    assert(len(q) == 4)
    if quat_conv == 'WXYZ':
        w, x, y, z = q
    elif quat_conv == 'XYZW':
        x, y, z, w = q
    else:
        raise RuntimeError("Convention {} not supported".format(quat_conv))

    return np.array([
        [1 - 2 * (y**2 + z**2), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x**2 + z**2), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x**2 + y**2)]])


def corners3d_outside_image(box, width, height):
    for vertex in box:
        if not ((0 <= vertex[0] < height) and (0 <= vertex[1] < width)):
            return True
    return False


def _draw_2d_bbox(ax, bboxes):
    """
    Draw 2d bbox for given obj bboxes in given figure axis
    """
    box = bboxes['corners2d'].flatten()
    rect = ptc.Rectangle(
        box[0:2], box[2] - box[0], box[3] - box[1],
        edgecolor='r', facecolor='none')
    ax.add_patch(rect)


def _draw_3d_bbox(bboxes):
    """Plot 3d bbox of given object bboxes to current plot"""
    bbox = bboxes['corners3d']
    for i in range(1, len(bbox)):
        for j in range(i + 1, len(bbox)):
            x1, y1 = int(bbox[i][0]), int(bbox[i][1])
            x2, y2 = int(bbox[j][0]), int(bbox[j][1])
            plt.plot([x1, x2], [y1, y2])


def plot_sample(sample, target='all', plot_2d_box=False, plot_3d_box=False):
    """Visual inspection of samples from dataset

    Args:
        sample({}): dataset sample
    
    Optional Args:
        *target(str): define image to plot (all, rgb, depth, mask, backdrop). Default: 'all'
        *plot_2d_box(bool): look for and try to plot 2d bounding box. Default: True
        *plot_3d_box(bool): look for and try to plot 3d bounding box. Default: False
    """
    # plot
    plt.figure(0)
    plt.clf()
    if target == 'all':
        ax = plt.subplot(2, 2, 1)
        # plot rgb
        plt.imshow(sample['images']['rgb'])
        # draw bboxes
        for obj in sample['objects']:
            if plot_2d_box:
                _draw_2d_bbox(ax, obj['bboxes'])
            if plot_3d_box:
                _draw_3d_bbox(obj['bboxes'])
        # plot depth
        plt.subplot(2, 2, 2)
        plt.imshow(sample['images']['depth'])
        # plot mask
        plt.subplot(2, 2, 3)
        plt.imshow(sample['images']['mask'])
        # plot backdrop
        plt.subplot(2, 2, 4)
        plt.imshow(sample['images']['backdrop'])
    else:
        ax = plt.subplot(1, 1, 1)
        # only rgb
        if target == 'rgb':
            plt.imshow(sample['images']['rgb'])
            # draw bboxes
            for obj in sample['objects']:
                if plot_2d_box:
                    _draw_2d_bbox(ax, obj['bboxes'])
                if plot_3d_box:
                    _draw_3d_bbox(obj['bboxes'])
        # only depth
        elif target == 'depth':
            plt.imshow(sample['images']['depth'])
        elif target == 'mask':
            plt.imshow(sample['images']['mask'])
        elif target == 'backdrop':
            plt.imshow(sample['images']['backdrop'])
        else:
            raise ValueError(f'Unknown target {target}')
    plt.show(block=True)
    plt.close()
