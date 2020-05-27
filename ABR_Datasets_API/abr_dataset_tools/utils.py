#!/usr/bin/env python

import os
from configparser import ConfigParser
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as ptc


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
        raise FileNotFoundError("Dataset configuration file {cfg_path} is missing / does not exists")
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
        RuntimeError: dataset relative to given config not rendered with ABR
    """
    render_setup = dict()
    render_setup['backend'] = str(cfg['backend'])
    if render_setup['backend'] == 'blender-cycles':
        render_setup['samples'] = float(cfg['samples'])
        render_setup['integrator'] = str(cfg['integrator'])
        render_setup['denoising'] = bool(cfg['denoising'])
    else:
        raise RuntimeError('Loading dataset which have not been rendered with ABR')
    
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
    dataset_info['base_dir'] = str(cfg['base_path'])
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
            'depth': os.path.join(root, 'Images', 'depth'),
            'mask': os.path.join(root, 'Images', 'mask')
        }
    }

    return dir_info


def build_camera_info(cfg):
    """ 
    Build cameare information from parsed configuration

    Args:
        cfg(configParser section): camera configuration

    Returns:
        dict with camera info

    Raises:
        ValueError: camera convention not valid
    """
    cam_info = {
        'name': str(cfg.get('name', 'Pinhole Camera')),
        'model': str(cfg.get('model', 'pinhole')),
        'uid': str(cfg.get('uid', '')),
        'width': cfg.getfloat('width'),
        'height': cfg.getfloat('height'),
        'zeroing': np.fromstring(cfg.get('zeroing', '0, 0, 0'), sep=',', dtype=np.float32),
        'convention': str(cfg.get('convention', 'opencv')),
        'dist_coeff': np.fromstring(cfg.get('distorsion', '0, 0, 0, 0, 0'), sep=',', dtype=np.float32)
    }

    # extrinsic parameters [q, t]
    extrinsic = np.fromstring(cfg.get('extrinsic', '0, 0, 0, 1, 0, 0, 0'), sep=',', dtype=np.float32)
    rotation = quaternion_to_rotation_matrix(extrinsic[3:], quat_conv='WXYZ')
    pose_w2c = np.eye(4)
    pose_w2c[0:3, 0:3] = rotation
    pose_w2c[0:3, 3] = extrinsic[:3]
    cam_info['pose_w2c'] = pose_w2c

    # build intrinsic matrix
    intrinsic = np.fromstring(cfg['intrinsic'], sep=',', dtype=np.float32).tolist()
    assert len(intrinsic) >= 4
    if len(intrinsic) == 4:
        intrinsic.append(0)
    fx, fy, cx, cy, skew = intrinsic
    cam_info.update({
        'fx': fx,
        'fy': fy,
        'cx': cx,
        'cy': cy,
        'skew': skew
    })

    # set camera matrix
    if cam_info['convention'] == 'opencv':
        cam_info['K'] = np.array([
            [fx, skew, cx],
            [0, fy, cy],
            [0, 0, 1]], dtype=np.float)
    elif cam_info['convention'] == 'opengl':
        cam_info['K'] = np.array([
            [fx, 0, 0],
            [0, fy, 0],
            [0, 0, -1]], dtype=np.float)
    else:
        raise ValueError('Unknown convention {}'.format(cam_info['convention']))
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
        *target(str): define image to plot (all, rgb, depth, mask). Default: 'all'
        *plot_2d_box(bool): look for and try to plot 2d bounding box. Default: True
        *plot_3d_box(bool): look for and try to plot 3d bounding box. Default: False
    """
    # plot
    plt.figure(0)
    plt.clf()
    if target == 'all':
        ax = plt.subplot(1, 3, 1)
        # plot rgb
        plt.imshow(sample['images']['rgb'])
        # draw bboxes
        for obj in sample['objects']:
            if plot_2d_box:
                _draw_2d_bbox(ax, obj['bboxes'])
            if plot_3d_box:
                _draw_3d_bbox(obj['bboxes'])
        # plot depth
        plt.subplot(1, 3, 2)
        plt.imshow(sample['images']['depth'])
        # plot mask
        plt.subplot(1, 3, 3)
        plt.imshow(sample['images']['mask'])
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
        else:
            raise ValueError('Unknown target {target}')
    plt.show(block=True)
    plt.close()
