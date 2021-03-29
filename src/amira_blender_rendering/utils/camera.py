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

import bpy
from mathutils import Vector, Matrix
from math import radians, atan2
import numpy as np
import os
import cv2

from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.math.curves import points_on_viewsphere, points_on_bezier, points_on_circle, \
    points_on_wave, random_points, points_on_piecewise_line, MultiviewModeConfiguration
from amira_blender_rendering.datastructures import Configuration
import amira_blender_rendering.utils.blender as blnd
# from amira_blender_rendering.utils.io import write_numpy_image_buffer, read_numpy_image_buffer

logger = get_logger()


class CameraGroupConfiguration(Configuration):
    """Class to handle camera group configurations"""

    def __init__(self, name='default_camera_group'):
        super(CameraGroupConfiguration, self).__init__(name=name)

        self.add_param(
            'model',
            'pinhole',
            'Camera model type'
        )
        self.add_param(
            'zeroing',
            [0.0, 0.0, 0.0],
            'Default camera zeroing rotation in degrees'
        )
        self.add_param(
            'intrinsic',
            [],
            'camera intrinsics fx, fy, cx, cy, possible altered via blender during runtime.',
        )
        self.add_param(
            'sensor_width',
            0.0,
            'Sensor width in mm (if not available, set to 0.0)'
        )
        self.add_param(
            'focal_length',
            0.0,
            'Focal length in mm (if not available, set to 0.0)'
        )
        self.add_param(
            'hfov',
            0.0,
            'Horizontal Field-of-View of the camera in degrees (if not available, set to 0.0)'
        )
        self.add_param(
            'intrinsics_conversion_mode',
            'mm',
            'Determine how to compute camera setup from intrinsics. One of "fov", "mm". Default: "mm"'
        )
        self.add_param(
            'type',
            'default',
            'Type of camera group. Based on this cameara operations are handled differently'
        )
        self.add_param(
            'names',
            ['Camera'],
            'List of names of bpy camera objects in the group'
        )
        self.add_param(
            'center',
            '',
            'Name of blender "empty" object used as center location for the group. If not given, use camera location'
        )
        self.add_param(
            'aim',
            '',
            'Name of blender "empty" object used as camera aim for the group (where to look at)'
        )
        self.add_param(
            'displacements_mm',
            [0.0],
            '(List of) relative x-axis (left, right) displacements (in mm) from center in local coordinate'
        )
        self.add_param(
            'compute_disparity',
            False,
            'If True, compute disparity map during postprocessing'
        )
        self.add_param(
            'baseline_mm',
            0.0,
            'Baseline distance between camera for disparity computation'
        )


def opengl_to_opencv(v: Vector) -> Vector:
    """Turn a coordinate in OpenGL convention to OpenCV convention.

    OpenGL's (and blenders) coordinate system has x pointing right, y pointing
    up, z pointing backwards.

    OpenCV's coordinate system has x pointing right, y pointing down, z pointing
    forwards."""
    if len(v) != 3:
        raise Exception(f"Vector {v} needs to be 3 dimensional")

    return Vector((v[0], -v[1], -v[2]))


def get_sensor_fit(sensor_fit, size_x, size_y):
    # determine most likely sensor fit
    if sensor_fit == 'AUTO':
        return 'HORIZONTAL' if size_x >= size_y else 'VERTICAL'
    else:
        return sensor_fit


def get_calibration_matrix(scene, cam):
    """Compute the calibration matrix K for a given scene and camera.

    Args:
        scene (bpy.types.Scene): scene to operate on
        cam (bpy.types.Camera): camera to compute calibration matrix for
    """
    fx, fy, cx, cy = get_intrinsics(scene, cam)
    K = Matrix(((fx, 0, cx), (0, fy, cy), (0, 0, 1)))
    return K


def _intrinsics_to_numpy(camera_info):
    """Convert the configuration values of `camera_info.intrinsics` to a numpy format"""
    if isinstance(camera_info.intrinsic, str):
        return np.fromstring(camera_info.intrinsic, sep=',', dtype=np.float32)
    elif isinstance(camera_info.intrinsic, list):
        if len(camera_info.intrinsic) == 0:
            return None
        else:
            return np.asarray(camera_info.intrinsic, dtype=np.float32)
    else:
        return None


def set_camera_info(scene, cam, camera_info, width: int = 0, height: int = 0):
    """Set the camera information of camera `cam` in scene `scene`.

    Note that this might set the render information, too. That is, resolution_x,
    resolution_y, resolution_percentage, pixel_aspect_x, and pixel_aspect_y will
    be affected by calling this function if intrinsics, stored in camera_info,
    is not None and no explicit values (>0) for width and height are specified.

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        camera_info (Configuration): camera_info configuration block of a configuration file

    Opt Args:
        width(int): render resolution along x axis. Default: 0
        height(int): render resolution along y axis. Default: 0
    """
    # get numpy version of the intrinsics, if possible
    intrinsics = _intrinsics_to_numpy(camera_info)

    # get all other values that might be of interest to shorten variable names
    sensor_width = camera_info.sensor_width
    focal_length = camera_info.focal_length
    hfov = camera_info.hfov

    # "Heuristically" determine how the user wants to set the camera
    # information.
    #
    # If the user provided sensor width and focal length, we can directly set
    # them for the camera and do not need to fall back to intrinsics
    if (sensor_width > 0.0) and (focal_length > 0.0):
        if (width == 0 or height == 0):
            if intrinsics is None:
                raise RuntimeError(
                    "Specify camera_info.width and camera_info.height or camera_info.intrinsics to set image sizes.")
            else:
                _setup_render_size_from_intrinsics(scene, intrinsics)
        logger.info("Setting camera information from sensor_width and focal_length")
        _setup_camera_by_swfl(scene, cam, sensor_width, focal_length)

    # If, the user specified a field of view, we can also directly set the
    # field of view. This might lead to different results for the sensor width
    # and height than an original sensor, but should yield the same rendering
    # results
    elif hfov > 0.0:
        if (width == 0 or height == 0):
            if intrinsics is None:
                raise RuntimeError(
                    "Specify camera_info.width and camera_info.height or camera_info.intrinsics to set image sizes.")
            else:
                _setup_render_size_from_intrinsics(scene, intrinsics)
        logger.info("Setting camera information from hFOV")
        _setup_camera_by_hfov(scene, cam, radians(hfov))

    # if the user did not specify (sensor width & focal length) || (fov), then
    # we will use the intrinsics to compute the field of view
    elif intrinsics is not None:
        mode = camera_info.intrinsics_conversion_mode.lower()
        if mode == 'fov':
            logger.info("Setting camera information from intrinsics using mode 'fov'")
            _setup_camera_intrinsics_to_fov(scene, cam, intrinsics)
        elif mode == 'mm':
            logger.info("Setting camera information from intrinsics using mode 'mm'")
            _setup_camera_intrinsics_to_mm(scene, cam, intrinsics)
        else:
            raise RuntimeError(
                f"Invalid mode '{mode}' to convert intrinsics. Needs to be either 'mm' (default) or 'fov'.")

    # if the user specified nothing at all, we will check if the width and
    # height of the image are set. In this case, the user will get the default
    # blender camera. If also width and height are 0, we will raise an
    # exception.
    # raise RuntimeError("Encountered invalid value for camera_info.intrinsic")
    elif (width == 0) or (height == 0):
        raise RuntimeError(
            "Invalid value camera_info setup. Specify intrinsics, sensor_width + focal length, hfov, or width + height")


def _setup_render_size_from_intrinsics(scene, intrinsics):
    """Set the render output size from camera intrinsics.

    Args:
        scene (bpy.types.Scene): scene to operate in
        intrinsics (np.array): intrinsics in order fx, fy, cx, cy
    """
    fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]
    render = scene.render

    # we assume that we render at 100% scale
    scale = 1.0

    # we assume that the principal point is in the center of the camera
    resolution_x = cx * 2.0
    resolution_y = cy * 2.0
    pixel_aspect_ratio = fx / fy

    # set render setup
    render.resolution_x = resolution_x / scale
    render.resolution_y = resolution_y / scale
    render.resolution_percentage = scale * 100
    render.pixel_aspect_x = 1.0
    render.pixel_aspect_y = pixel_aspect_ratio


def _setup_camera_by_swfl(scene, cam, sensor_width, focal_length):
    """Setup the camera by sensor width and focal length

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        sensor_width (float): sensor width in mm
        focal_length (float): focal length of the sensor in mm
    """
    cam.type = 'PERSP'
    cam.sensor_fit = 'HORIZONTAL'
    cam.lens_unit = 'MILLIMETERS'
    cam.lens = focal_length  # 1 is the min possible value
    cam.sensor_width = sensor_width


def _setup_camera_by_hfov(scene, cam, hfov):
    """Setup the camera by sensor width and focal length

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        hfov (float): horizontal field-of-view in degrees
    """
    cam.type = 'PERSP'
    cam.sensor_fit = 'HORIZONTAL'
    cam.lens_unit = 'FOV'
    cam.lens = hfov


def _setup_camera_intrinsics_to_mm(scene, cam, intrinsics):
    """Set the camera intrinsics of a camera.

    Note that this will set the render information, too. That is, resolution_x,
    resolution_y, resolution_percentage, pixel_aspect_x, and pixel_aspect_y will
    be affected by calling this function.

    Note also that the implementation is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://www.rojtberg.net/1601/from-blender-to-opencv-camera-and-back/ and
        3) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        intrinsics (np.array): camera intrinsics in the order fx, fy, cx, cy
    """
    fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]

    # we assume a horizontal sensor with a default height of 1.0, so we only need to set one sensor size
    sensor_size_mm = fy * cx / (fx * cy)

    # compute focal lengths s_u, s_v
    resolution_x = cx * 2.0
    # resolution_y = cy * 2.0
    s_u = resolution_x / sensor_size_mm
    # s_v = resolution_y / 1.0

    # compute camera focal length in mm
    f_in_mm = fx / s_u

    # setup render output sizes
    _setup_render_size_from_intrinsics(scene, intrinsics)

    # set to perspective camera with computed focal length and sensor size
    _setup_camera_by_swfl(scene, cam, sensor_size_mm, f_in_mm)


def _setup_camera_intrinsics_to_fov(scene, cam, intrinsics):
    """Set the camera intrinsics of a camera via intermediate computation of the
    FOV.

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        intrinsics (np.array): camera intrinsics in the order fx, fy, cx, cy
    """
    # fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]
    fx, _, cx, _ = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]

    # extract field of view
    resolution_x = cx * 2.0
    # resolution_y = cy * 2.0
    fovx = atan2(cx, fx) + atan2(resolution_x - cx, fx)
    # fovy = atan2(cy, fy) + atan2(resolution_y - cy, fy)

    # set render output size
    _setup_render_size_from_intrinsics(scene, intrinsics)

    # set the camera with computed angle
    # TODO: at the moment we don't check which angle is larger. Blender expects
    # the larger angle to be set. Before changing this, we should evaluate if
    # this behavior is correct for all our use-cases, thought
    _setup_camera_by_hfov(scene, cam, fovx)


def get_intrinsics(scene, cam):
    """Get the camera intrinsics of a camera

    Note that this code is inspired by
        1) https://ksimek.github.io/2013/08/13/intrinsic/ and
        2) https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera

    Args:
        scene (bpy.types.Scene): scene to operate on
        cam (bpy.types.Camera): camera to compute calibration matrix for

    Returns:
        Tuple (fx, fy, cx, cy) of the focal lengths and the camera's principal
        point coordinates.
    """
    if cam.type != 'PERSP':
        raise ValueError('Invalid camera type. Calibration matrix can be computed only for perspective cameras.')

    render = scene.render

    # get resolution information
    f_in_mm = cam.lens
    scale = scene.render.resolution_percentage / 100
    resolution_y = scale * render.resolution_y
    resolution_x = scale * render.resolution_x

    # extract additional sensor information (size in mm, sensor fit)
    sensor_size_mm = cam.sensor_height if cam.sensor_fit == 'VERTICAL' else cam.sensor_width
    sensor_fit = get_sensor_fit(cam.sensor_fit, render.pixel_aspect_x * resolution_x,
                                render.pixel_aspect_y * resolution_y)

    # compute pixel size in mm per pixel
    pixel_aspect_ratio = render.pixel_aspect_y / render.pixel_aspect_x
    view_fac_in_px = resolution_x if sensor_fit == 'HORIZONTAL' else resolution_y * pixel_aspect_ratio
    pixel_size_mm_per_px = sensor_size_mm / f_in_mm / view_fac_in_px

    # compute focal length in x and y direction (s_u, s_v)
    s_u = 1.0 / pixel_size_mm_per_px
    s_v = 1.0 / pixel_size_mm_per_px / pixel_aspect_ratio

    # compute intrinsic parameters of K
    u_0 = resolution_x / 2 - cam.shift_x * view_fac_in_px
    v_0 = resolution_y / 2 + cam.shift_y * view_fac_in_px / pixel_aspect_ratio

    # finalize K
    return s_u, s_v, u_0, v_0


def project_pinhole_range_to_rectified_depth(filepath_in: str, filepath_out: str,
                                             calibration_matrix: np.array,
                                             res_x: int = bpy.context.scene.render.resolution_x,
                                             res_y: int = bpy.context.scene.render.resolution_y,
                                             scale: float = 1e4):
    """
    Given a depth map computed (as standard in ABR setup) using a perfect pinhole model,
    compute the projected rectified depth

    The function assumes to read-in from an Exr image format (32 bit true range values)
    and to write-out in PNG image format (16 bit truncated depth values).

    NOTE: depth values that might cause overflow in 16bit (i.e. >65k) are set to 0.

    Args:
        filepath_in(str): path to (.exr) file with range values (assumed in m) to load
        filepath_out(str): path to (.png) file where (rectified) depth map is write to.
                           If None (explicitly given) only return converted image (no save).
                           NOTE: make sure the filesystem tree exists
        calibration_matrix(np.array): 3x3 camera calibration matrix

    Optional Args:
        res_x(int): render/image x resolution (pixel). Default is initial scene resolution_x
        res_y(int): render/image y resolution (pixel). Default is initial scene resolution_y
        scale(float): scaling factor to convert range (in m) to depth. Default 1e4 (m to .1 mm)

    Return:
        np.array<np.uint16>: converted depth
    """
    # quick check file type
    if '.exr' not in filepath_in:
        raise ValueError(f'Given input file {filepath_in} not of type EXR')
    if filepath_out is not None and '.png' not in filepath_out:
        raise ValueError(f'Given output file {filepath_out} not of tyep PNG')
    if not os.path.exists(filepath_in):
        raise ValueError(f"File {filepath_in} does not exist. Please check path")

    # range_exr = read_numpy_image_buffer(filepath_in, True)
    range_exr = cv2.imread(filepath_in, cv2.IMREAD_ANYDEPTH)

    # perform transformation
    logger.info('Rectifying pinhole range map into depth')
    grid = np.indices((res_y, res_x))
    u = grid[1].flatten()
    v = grid[0].flatten()
    uv1 = np.array([u, v, np.ones(res_x * res_y)])

    K_inv = np.linalg.inv(calibration_matrix)
    v_dirs_mtx = np.dot(K_inv, uv1).T.reshape(res_y, res_x, 3)
    v_dirs_mtx_unit_inv = np.reciprocal(np.linalg.norm(v_dirs_mtx, axis=2))
    # transpose since depth is in WxH
    # v_dirs_mtx_unit_inv = v_dirs_mtx_unit_inv.transpose()
    depth_img = (range_exr * v_dirs_mtx_unit_inv * scale)
    # clip values in uint16 range
    depth_img = np.clip(depth_img, 0, np.iinfo(np.uint16).max)
    # compute normalized
    # depth_img_normalized = depth_img / np.iinfo(np.uint16).max
    # cast
    depth_img_uint16 = depth_img.astype(np.uint16)

    # write out if requested
    if filepath_out is not None:
        # write takes care of casting to uint16 from a normalized buffer
        cv2.imwrite(filepath_out, depth_img_uint16)
        # write_numpy_image_buffer(depth_img_normalized, filepath_out)
        logger.info(f'Saved (rectified) depth map at {filepath_out}')

    # cast unnormalized to uint16
    return depth_img_uint16


def compute_disparity_from_z_info(filepath_in: str, filepath_out: str,
                                  baseline_mm: float,
                                  calibration_matrix: np.array,
                                  res_x: int = bpy.context.scene.render.resolution_x,
                                  res_y: int = bpy.context.scene.render.resolution_y,
                                  scale: float = 1e4):
    """Compute disparity map from given z info (depth or range). Values are in .1 mm
    By convention, disparity is computed from left camera to right camera (even for the right camera).

    if z = depth, this is assumed to be stored as a PNG image of uint16 (compressed) values in .1 mm
    If z = range, this is assumed to be stored as a EXR image of float32 (true range) values in meters

    Args:
        fpath_in(str): path to input file to read in
        fpath_out(str): path to output file to write out. If None (explicitly given), only return (no save to file).
                        NOTE: make sure the filesystem tree exists
        baseline_mm(float): baseline value (in mm) between parallel cameras setup
        calibration_matrix(np.array): 3x3 camera calibration matrix. Used also to extract the focal lenght in pixel

    NOTE: if z = range, depth must be computed. This requires additional arguments.
          See  amira_blender_rendering.utils.camera.project_pinhole_range_to_rectified_depth

    Opt Args:
        res_x(int): render/image x resolution. Default: bpy.context.scene.resolution_x
        res_y(int): render/image y resolution. Default: bpy.context.scene.resolution_y
        scale(float): value used to convert range (in m) to depth. Default: 1e4 (.1mm)

    Returns:
        np.array<np.uint16>: disparity map in pixels
    """
    # check filepath_in to read file from
    if '.png' in filepath_in:
        logger.info(f'Loading depth from .PNG file {filepath_in}')
        # depth = read_numpy_image_buffer(filepath_in)
        depth = cv2.imread(filepath_in)

    elif '.exr' in filepath_in:
        # in case of exr file we convert range to depth first
        logger.info(f'Computing depth from EXR range file {filepath_in}')
        depth = project_pinhole_range_to_rectified_depth(
            filepath_in, None, calibration_matrix, res_x, res_y, scale)

    else:
        logger.error(f'Given file {filepath_in} is neither of type PNG nor EXR. Skipping!')
        return

    # depth is always converted to mm and to float for precision computations
    depth = depth.astype(np.float32) / (scale / 1e3)

    logger.info('Computing disparity map')
    # get focal lenght
    focal_length_px = calibration_matrix[0, 0]
    # disparity in pixels
    disparity = baseline_mm * focal_length_px * np.reciprocal(depth)
    # clip to 16 bit value range
    disparity = np.clip(disparity, 0, np.iinfo(np.uint16).max)
    # normalized buffer
    # disparity_normalized = disparity / disparity.max()
    # cast
    disparity_uint16 = disparity.astype(np.uint16)

    # write out if requested
    if filepath_out is not None:
        # write takes care of casting to 16 bit from a normalize buffer
        # write_numpy_image_buffer(disparity, filepath_out)
        cv2.imwrite(filepath_out, disparity_uint16)
        logger.info(f'Saved disparity map at {filepath_out}')

    # cast and return
    return disparity_uint16


def get_camera_location(cam_name: str):
    """
    Return 3d location of selected camera

    Args:
        cam_name(str): name of camera blender object

    Returns:
        array with location
    """
    camera = bpy.context.scene.objects[cam_name]
    return np.asarray(camera.matrix_world.to_translation())


def get_camera_pose(cam_name: str):
    """
    Return 3d pose of selected camera

    Args:
        cam_name(str): name of camera blender object

    Returns:
        array with 4-dim pose matrix
    """
    camera = bpy.context.scene.objects[cam_name]
    return np.asarray(camera.matrix_world)


def generate_multiview_locations(num_locations: int, mode: str, **kw):
    """
    Generate multiple 3d locations based on the selected mode

    Args:
        num_locations(int): number of locations to generate
        mode(str): mode used to generate locations

    Keywords Args:
        config(Configuration/dict-like)
        offset(array(3,)): if given, it is addedd to all generated locations. Default [0, 0, 0]

    Returns:
        locations(array-like): generated locations
    """

    # define supported modes
    # TODO: register functions
    _available_modes = {
        'random': random_points,
        'bezier': points_on_bezier,
        'circle': points_on_circle,
        'wave': points_on_wave,
        'viewsphere': points_on_viewsphere,
        'piecewiselinear': points_on_piecewise_line,
    }

    # early check for selected mode
    if mode not in _available_modes.keys():
        raise ValueError(f'Selected mode {mode} not supported for multiview locations')

    # build dict with available config per each mode
    mode_cfg = MultiviewModeConfiguration()[mode].right_merge(kw.get('config', Configuration()))
    # check for given offest
    offset = kw.get('offset', np.array([0, 0, 0]))
    # repeat along axis
    offset = np.repeat(offset.reshape(1, -1), num_locations, axis=0)
    # generate locations according to selected mode and add offset
    locations = offset + _available_modes[mode](num_locations, **mode_cfg.todict())
    return locations


def compute_cameras_poses(camera_groups, config, locations, offset: bool = True):
    """Given a list of absoluted locations compute camera poses
    for given list of camera groups

    The methods works differently depending on the camera group type.
    Currently we support computations for the following types:
        - `standalone`: floating cameras that are supposed to work on their own (monocular view).
            In this case, users can specify a center object which is used to track the given list
            of 3d locations while aiming at the specificed aim object.
            In addition, diplacement_mm can be used to move the camera left/right wrt to the center location.
            In this case, if a center object is not given, each camera is used as its center.

        - `non_parallel_stereo`: stereo setup not subject to epipolar constraints.
            The stero cameras are rotated inwards towards a common aim object.
            In this case users *must* specify a center object for the group.
            Camera locations are set relative to the center location. In particular, each camera is displaced along
            the local x-axis (left-right) of the center object according to the value stored in displacement_mm.
            Camera rotations track the given aim so that each camera always "look-at" it.

        - `parallel_stereo`: stereo setup subject to epipolar constraints
            In this case users *must* specify a center for the camera group.
            The center is used to track the given list of 3d locations while aiming at the specified aim object.
            Camera rotations are set equal to the center rotation to ensure epipolar constraint between cameras.

        NOTE: `standalone` and `non_parallel_stereo` types behaves similarly. However, while standalone cameras
        are logically treated as separate, stereo cameras are logically considered as part of the same setup.

    Args:
        camera_grops([str]): list with names of camera groups
        config(Configuration): structure with camera config for each group
        locations([array]): list of absolute 3d location for the center of the camera group

    Opt Args:
        offset(bool): if True (default), locations are offset by the center group original location

    Returns:
        cameras_poses(dict): dictionary of poses for each camera in all groups

    NOTE: be careful since the method affects active constraints on the cameras
    """

    def _apply():
        # apply constraint
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

    # init poses dict
    cameras_poses = {}

    # loop over each camera group
    for grp in camera_groups:
        grp_cfg = config[grp]

        cam_aim = grp_cfg.aim
        cam_type = grp_cfg.type
        cam_names = grp_cfg.names
        displacements_mm = grp_cfg.displacements_mm  # This needs to be adjusted

        # init center object container
        cnt_obj_original = None

        # loop over cameras in group
        for cam_idx, cam_name in enumerate(cam_names):

            # init list of poses for camera
            if cam_name not in cameras_poses:
                cameras_poses[cam_name] = []

            # get center object, if none given (depending on the type),
            # create an empty and place it on the current camera location
            cam_center = grp_cfg.center
            if cam_center == '':
                if cam_type in ['parallel_stereo', 'non_parallel_stereo']:
                    raise ValueError(f'Camera group of type "{cam_type}" requires a center object')
                cam_center = f'Tmp{cam_name}Center'
                # see if already created otherwise create
                cnt_obj = blnd.select_object(cam_center)
                if cnt_obj is None:
                    # get camera
                    cam_obj = blnd.select_object(cam_name)
                    # create empty at camera location
                    bpy.ops.object.empty_add(
                        type='PLAIN_AXES',
                        align='WORLD',
                        location=cam_obj.matrix_world.to_translation().copy(),
                        scale=(.1, .1, .1))
                    bpy.context.active_object.name = cam_center
                    cnt_obj = blnd.select_object(cam_center)
                    _apply()

            # select
            cnt_obj = blnd.select_object(cam_center)

            # clear constraints from camera to allow correct positioning afterwards
            blnd.select_object(cam_name).constraints.clear()

            # add "track to" constraint to make center "look at" corresponding aim
            cnt_obj.constraints.clear()  # clear all constraints first
            cnt_obj.constraints.new(type='TRACK_TO')
            cnt_obj.constraints['Track To'].target = bpy.data.objects[cam_aim]
            cnt_obj.constraints['Track To'].track_axis = 'TRACK_NEGATIVE_Z'
            cnt_obj.constraints['Track To'].up_axis = 'UP_Y'
            _apply()

            # copy center to avoid overwriting information
            if cnt_obj_original is None:
                blnd.select_object(cam_center)
                bpy.ops.object.duplicate()
                cnt_obj_original = bpy.context.object
            else:
                cnt_obj.matrix_world.col[3][:3] = cnt_obj_original.matrix_world.to_translation().copy()
                _apply()

            # get center pose
            M_wld2cnt = cnt_obj.matrix_world

            # get origin offset
            origin = np.asarray(M_wld2cnt.to_translation().copy()) if offset else np.zeros(3,)

            # loop over all desired locations
            for location in locations:

                # move center to desired location
                M_wld2cnt.col[3][:3] = origin + location
                _apply()

                # for each location, compute the absolute camera pose depending on cam_type
                if cam_type in ['standalone', 'non_parallel_stereo']:
                    # get displacement in center coordinats
                    M_cnt2cam = Matrix()
                    M_cnt2cam[0][3] = 1e-3 * displacements_mm[cam_idx]
                    # compute translation
                    t_wld2cam = (M_wld2cnt @ M_cnt2cam).to_translation()
                    # shift camera: this modifies also the rotations since the center tracks the aim
                    M_wld2cnt.col[3][:3] = t_wld2cam
                    _apply()
                    # save pose
                    cameras_poses[cam_name].append(M_wld2cnt.copy())

                elif cam_type == 'parallel_stereo':
                    # get camera pose in center coordinate system
                    M_cnt2cam = Matrix()
                    M_cnt2cam[0][3] = 1e-3 * displacements_mm[cam_idx]
                    # compute camera pose in world coordiante system
                    M_wld2cam = M_wld2cnt @ M_cnt2cam
                    # save camera pose
                    cameras_poses[cam_name].append(M_wld2cam)

                else:
                    raise ValueError(f'Given camera type "{cam_type}" is not supported.')

        # make sure to clear the constraints
        # This is needed since in case cnt_obj == camera the active constraint could
        # compromise positioning of the camera
        cnt_obj.constraints.clear()

    return cameras_poses
