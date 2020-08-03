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

from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.math.curves import points_on_viewsphere, points_on_bezier, points_on_circle, \
    points_on_wave, plot_points, random_points
from amira_blender_rendering.datastructures import Configuration


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


def set_camera_info(scene, cam, camera_info):
    """Set the camera information of camera `cam` in scene `scene`.

    Note that this might set the render information, too. That is, resolution_x,
    resolution_y, resolution_percentage, pixel_aspect_x, and pixel_aspect_y will
    be affected by calling this function if intrinsics, stored in camera_info,
    is not None.

    Args:
        scene (bpy.types.Scene): scene to operate in
        cam (bpy.types.Camera): camera to modify
        camera_info (Configuration): camera_info configuration block of a configuration file
    """

    logger = get_logger()

    # get numpy version of the intrinsics, if possible
    intrinsics = _intrinsics_to_numpy(camera_info)

    # get all other values that might be of interest to shorten variable names
    width = camera_info.width
    height = camera_info.height
    sensor_width = camera_info.sensor_width
    focal_length = camera_info.focal_length
    hfov = camera_info.hfov

    #
    # "Heuristically" determine how the user wants to set the camera
    # information.
    #
    # If the user provided sensor width and focal length, we can directly set
    # them for the camera and do not need to fall back to intrinsics
    if (sensor_width > 0.0) and (focal_length > 0.0):
        if (width == 0 or height == 0):
            if intrinsics is None:
                raise RuntimeError(
                    "Please specify camera_info.width and camera_info.height or camera_info.intrinsics to set image sizes.")
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
                    "Please specify camera_info.width and camera_info.height or camera_info.intrinsics to set image sizes.")
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
            "Encountered invalid value camera_info setup. Please specify intrinsics, sensor_width + focal length, hfov, or width + height")


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
    cam.lens = focal_length
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
    resolution_y = cy * 2.0
    s_u = resolution_x / sensor_size_mm
    s_v = resolution_y / 1.0

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
    fx, fy, cx, cy = intrinsics[0], intrinsics[1], intrinsics[2], intrinsics[3]

    # extract field of view
    resolution_x = cx * 2.0
    resolution_y = cy * 2.0
    fovx = atan2(cx, fx) + atan2(resolution_x - cx, fx)
    fovy = atan2(cy, fy) + atan2(resolution_y - cy, fy)

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


def project_pinhole_depth_to_rectilinear(filepath: str, outfilepath: str,
                                         res_x: int = bpy.context.scene.render.resolution_x,
                                         res_y: int = bpy.context.scene.render.resolution_y,
                                         sensor_width: float = bpy.context.scene.camera.data.sensor_width,
                                         f_in_mm: float = bpy.context.scene.camera.data.lens):
    """
    Given a depth map computed (as standard in ABR setup) using a perfect pinhole model,
    compute the projected rectilinear depth
    
    Args:
        filepath(str): path to file with depth map to load
        outfilepath(str): path to write rectfied map to
        res_x(int): render/image x resolution
        res_y(int): render/image y resolution
        sensor_width(float): camera sensor width
        f_in_mm(float): camera focal lenght in mm
    """
    import cv2
    logger = get_logger()

    sensor_height = res_y / res_x * sensor_width

    # read image
    image = (cv2.imread(filepath, cv2.IMREAD_ANYDEPTH)).astype(np.float32)

    # init array
    rect_depth = np.zeros(image.shape, dtype=np.float32)
    
    logger.info('Rectifying pinhole depth map')
    for u in range(image.shape[1]):
        for v in range(image.shape[0]):

            d = image[v, u]

            # if d > 100.0:
            #     continue

            # coordinates on camera plane
            x = (0.5 - float(u) / float(image.shape[1])) * sensor_width / f_in_mm
            y = (0.5 - float(v) / float(image.shape[0])) * sensor_height / f_in_mm
            z = 1.0
            norm = np.linalg.norm([x, y, z])

            # normalize = project point on unit sphere, then apply depth
            z = d * z / norm
            
            # fill depth map
            rect_depth[v, u] = z
    
    # overwrite file
    cv2.imwrite(outfilepath, rect_depth, [cv2.IMWRITE_EXR_TYPE, cv2.IMWRITE_EXR_TYPE_FLOAT])
    logger.info(f'Saved rectified depth map at {outfilepath}')


def generate_multiview_cameras_locations(num_locations: int, mode: str, camera_names: list, **kw):
    """
    Generate multiple locations for multiple cameras according to selected mode

    Args:
        num_locations(int): number of locations to generate
        mode(str): mode used to generate locations
        camera_names(list(str)): list of string with camera names
    
    Keywords Args:
        config(Configuration/dict-like)
        debug(bool): it True, plot 3D generated locations for visual debug
        plot_axis(bool): if debug, plot camera coordinate systems on 3D locations
        scatter(bool): if debug, if True, enable scatter plot

    Returns:
        locations(dict(array)): dictionary with list of locations for each camera
        original_locations(dict(array)): dictionary with original camera locations
    """

    def get_array_from_str(cfg, name, default):
        """
        Get array from a csv string or fallback to default

        Args:
            cfg(dict-like): configuration struct where to look
            name(str): config parameter to search for
            default(array-like): default array value
        
        Returns:
            array-like: found in cfg or default
        """
        p = cfg.get(name, default)
        if isinstance(p, str):
            p = np.fromstring(p, sep=',')
        return p

    # get logger
    logger = get_logger()
    debug = kw.get('debug', False)
    plot_axis = kw.get('plot_axis', False)
    scatter = kw.get('scatter', False)

    # save original camera locations
    original_locations = {}
    for cam_name in camera_names:
        camera = bpy.context.scene.objects[cam_name]
        original_locations[cam_name] = np.asarray(camera.matrix_world.to_translation())

    # define supported modes
    _available_modes = {
        'random': random_points,
        'bezier': points_on_bezier,
        'circle': points_on_circle,
        'wave': points_on_wave,
        'viewsphere': points_on_viewsphere
    }

    # early check for selected mode
    if mode not in _available_modes.keys():
        raise ValueError(f'Selected mode {mode} not supported for multiview locations')

    # build dict with available config per each mode
    mode_cfg = kw.get('config', Configuration())  # get user defined config (if any)
    _modes_cfgs = {
        'random': {
            'base_location': get_array_from_str(mode_cfg, 'base_location', original_locations[cam_name]),
            'scale': float(mode_cfg.get('scale', 1))
        },
        'bezier': {
            'p0': get_array_from_str(mode_cfg, 'p0', original_locations[cam_name]),
            'p1': get_array_from_str(mode_cfg, 'p1',
                                     original_locations[cam_name] + np.random.randn(original_locations[cam_name].size)),
            'p2': get_array_from_str(mode_cfg, 'p2',
                                     original_locations[cam_name] + np.random.randn(original_locations[cam_name].size)),
            'start': float(mode_cfg.get('start', 0)),
            'stop': float(mode_cfg.get('stop', 1))
        },
        'circle': {
            'radius': float(mode_cfg.get('radius', 1)),
            'center': get_array_from_str(mode_cfg, 'center', original_locations[cam_name])
        },
        'wave': {
            'radius': float(mode_cfg.get('radius', 1)),
            'center': get_array_from_str(mode_cfg, 'center', original_locations[cam_name]),
            'frequency': float(mode_cfg.get('frequency', 1)),
            'amplitude': float(mode_cfg.get('amplitude', 1))
        },
        'viewsphere': {
            'scale': float(mode_cfg.get('scale', 1)),
            'bias': tuple(get_array_from_str(mode_cfg, 'bias', [0, 0, 1.5]))
        }
    }

    # init container
    locations = {}

    # loop over cameras
    for cam_name in camera_names:

        # log
        logger.info(f'Generating locations for {cam_name} according to {mode} mode')

        # extract camera object
        camera = bpy.context.scene.objects[cam_name]
        
        # get location
        locations[cam_name] = _available_modes[mode](num_locations, **_modes_cfgs[mode])

        # for visual debug
        if debug:
            plot_points(np.array(locations[cam_name]), camera, plot_axis=plot_axis, scatter=scatter)

    return locations, original_locations
