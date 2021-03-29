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

"""Module containing base ABR scene class.
The class inherits from the ABC interface class defined in amira_blender_rendering.interfaces.IScene

It also implements additional basic functionalities useful to most ABR scenes
"""

import os
import bpy
import pathlib
from math import ceil, log
from amira_blender_rendering.utils.logging import get_logger
import amira_blender_rendering.utils.camera as camera_utils
import amira_blender_rendering.utils.blender as blnd
from amira_blender_rendering.utils.io import expandpath
import amira_blender_rendering.scenes as abr_scenes
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
from amira_blender_rendering.interfaces import IScene

logger = get_logger()


def _setup_logpath_on_error(logpath: str):
    "Add current time to given logpath"
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    return os.path.join(logpath, now)


def _save_data_on_error(scn_str, view_str, rgb_base_path, mask_base_path, logpath, objs):
    "Save additional images to file"
    from shutil import copyfile
    logger.error('Saving to blender on error. Dumping additional image data')
    # copy rgb
    rgbname = scn_str[1:] + view_str + '.png'
    srcpath = os.path.join(rgb_base_path, rgbname)
    dstpath = os.path.join(logpath, rgbname)
    copyfile(srcpath, dstpath)
    # copy masks
    for obj in objs:
        maskname = scn_str[1:] + view_str + f'{obj["id_mask"]}.png'
        srcpath = os.path.join(mask_base_path, maskname)
        dstpath = os.path.join(logpath, maskname)
        copyfile(srcpath, dstpath)


def _save_camera_poses_to_blend(name: str, poses: list, filepath: str):
    """Given a camera and a list of world poses, a copy of the camera
    in each one of the given pose in a blender file.

    Args:
        name(str): camera name as in the prescribed blender file
        poses(list): list of camera world poses
        filepath(str): path where .blend file is saved
    """
    if name is None or poses is None:
        logger.warn('Either given camera name or poses are None. To dump both must be given. Skipping')
        return

    # create and link temporary collection
    tmp_cam_coll = bpy.data.collections.new('TemporaryCameras')
    bpy.context.scene.collection.children.link(tmp_cam_coll)

    tmp_cameras = []
    for pose in poses:
        blnd.select_object(name)
        bpy.ops.object.duplicate()
        # TODO: remove from original collection to avoid name clutter in .blend
        tmp_cam_obj = bpy.context.object
        tmp_cam_obj.matrix_world = pose
        tmp_cam_coll.objects.link(tmp_cam_obj)
        tmp_cameras.append(tmp_cam_obj)
    # update depsgraph to "apply" new pose
    bpy.context.evaluated_depsgraph_get().update()

    logger.info(f"Saving camera poses to blender file {filepath} for debugging")
    bpy.ops.wm.save_as_mainfile(filepath=filepath)

    # clear objects and collection
    bpy.ops.object.select_all(action='DESELECT')
    for tmp_cam in tmp_cameras:
        bpy.data.objects.remove(tmp_cam)
    bpy.data.collections.remove(tmp_cam_coll)


class BaseABRScene(IScene):
    """interface of functions that each sccene needs to adhere to"""
    def __init__(self):
        # get logger
        self.logger = get_logger()
        
        # we do composition here, not inheritance anymore because it is too
        # limiting in its capabilities. Using a render manager is a better way
        # to handle compositor nodes
        self.renderman = abr_scenes.RenderManager()

    def check_supported_render_modes(self, mode, supported_modes: list = ['default']):
        """For a given scene, check whether a render mode is supported or not.

        Args:
            mode(str): render mode to check
            supported_modes(list(str)): supported modes for the given scene
        
        Returns:
            None

        Raises:
            Value Error: if mode not in supported_modes
        """
        if mode not in supported_modes:
            raise ValueError(f'Requested mode "{mode}" not among supported: "{supported_modes}"')
        
    # handle multiple camera groups
    def load_camera_group_configs(self):
        """
        Iterate over selected camera groups and set up their config objects
        """
        for grp in self.config.scene_setup.camera_groups:
            # create a configuration for the group
            cfg = camera_utils.CameraGroupConfiguration()
            # right merge default values
            cfg.right_merge(self.config.default_camera_group)
            # right merge config values given in the config not yet parsed
            cfg.right_merge(self.config[grp])
            self.config[grp] = cfg  # overwrite group configuration
            del cfg
        
    def setup_compositor(self, objs, **kw):
        self.renderman.setup_compositor(objs, **kw)

    def setup_renderer(self):
        """
        Apply config values to the renderer

        NOTE: do this after setting up the scene otherwise values here will be ignored
        """
        self.renderman.setup_renderer(
            'CYCLES',  # TODO: this should not be hardcoded
            self.config.render_setup.integrator,
            self.config.render_setup.denoising,
            self.config.render_setup.samples,
            self.config.render_setup.motion_blur
        )
    
    def setup_dirinfo(self, camera_name: str):
        """Setup directory information for a given camera according to its name.

        Args:
            camera_name(str): name of camera for which directory information must be set up
        """
        # compute directory information for each of the cameras
        if not hasattr(self, 'dirinfos'):
            self.dirinfos = list()
        
        # paths are set up as: base_path + CameraName
        camera_base_path = os.path.join(self.config.dataset.base_path, camera_name)
        dirinfo = build_directory_info(camera_base_path)
        self.dirinfos.append(dirinfo)
    
    def setup_scene(self):
        """Set up the entire scene.
        As default behavior, we simply load the main blender file from disk.

        NOTE: modify as necessary by overwritting this method in your custom scene
        """
        bpy.ops.wm.open_mainfile(filepath=expandpath(self.config.scene_setup.blend_file))
        # we need to hide all dropboxes and dropzones in the viewport, otherwise
        # occlusion testing will not work, because blender's ray_cast method
        # returns hits no empties!
        self.logger.info("Hiding all dropzones from viewport")
        bpy.data.collections['Dropzones'].hide_viewport = True
    
    def setup_camera(self, cam_name, config, width=0, height=0):
        """Set up camera object according to given config values.
        NOTE: this does not select a camera for which to render. This will
        be selected elsewhere.
        
        Args:
            cam_name(str): name of camera object in blender scene
            config(Configuration): struct with configuration for selected camera
        """
        # grab the scene
        scene = bpy.context.scene
        # select the camera. Blender often operates on the active object, to
        # make sure that this happens here, we select it
        blender_camera = blnd.select_object(cam_name)
        # get camera data
        cam_data = blender_camera.data
        # set the calibration matrix
        camera_utils.set_camera_info(scene, cam_data, config, width=width, height=height)

    def setup_environment_textures(self):
        """
        Get a list of texture to be used as textures for the "world node" (aka the environment)
        from a given path
        """
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)
    
    def forward_simulate(self):
        scene = bpy.context.scene
        for i in range(self.config.scene_setup.forward_frames):
            self.logger.info(f"forward simulation of {i}/{self.config.scene_setup.forward_frames} frames")
            scene.frame_set(i + 1)
        self.logger.info('forward simulation: done!')

    def activate_camera(self, cam_name: str):
        """
        Set selected camera as active for the scene

        Args:
            cam_name(str): name of bpy camera object
        """
        # first get the camera name. this depends on the scene (blend file)
        bpy.context.scene.camera = bpy.context.scene.objects[cam_name]

    def dump_config(self):
        """Dump configuration to a file in the output folder(s).
        
        The default behavior is to dump config to each of the dir-info base locations,
        i.e. for each camera that was rendered we store the configuration

        NOTE: modify as necessary by overwriting the behavior in your custom scene
        """
        for dirinfo in self.dirinfos:
            output_path = dirinfo.base_path
            pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
            dump_config(self.config, output_path)

    def generate_dataset(self):
        raise NotImplementedError()

    def teardown():
        """Tear down scene. By default we do nothing.
        NOTE: overwrite as necessary in your custom scene
        """
        pass

    def save_to_blend(self, dirinfo, **kw):
        """
        Save debug data to .blend files

        The behavior of the method depends on its keywords input arguments.
        In particular:
            - with no optional args: it dump the current active scene to .blend in ActiveCamera/Logs
                                    where ActiveCamera identify the directory where data, i.e.,
                                    Images and Annotations, for the currently active camera are stored.
            - with camera_name and camera_poses: the active camera is duplicated and placed in all given poses.
                                                Use this behavior to check whether generated poses are valid.
            - with view_index and scene_index: the current active scene is logged to .blend
                                                following ABR base filenaming convention
                - if additionally on_error == True: data are logged to a separate timestamped subdirectory
                                                    (together with additional data) to avoid data overwrite

        NOTE: camera_name and camera_poses have priority. That is, if given, other kwargs are not considered.

        Args:
            dirinfo(dict-like/Configuration): struct with information about dataset filesystem

        Kwargs Args:
            camera_name(str): name for active camera, as appears in the active scene
            camera_poses(list): list containing multiple camera world poses
            scene_index(int): index of static scene being rendered
            view_index(int): index of current view being rendered
            on_error(bool): if True, assume an error has been raised and additional data are logged
        """
        # extract args
        basefilename = kw.get('basefilename', 'debug')
        
        camera_name = kw.get('camera_name', None)
        camera_poses = kw.get('camera_poses', None)

        scn_idx = kw.get('scene_index', None)
        view_idx = kw.get('view_index', None)
        on_error = kw.get('on_error', False)

        # extract and  (if necessary) create log directory
        logpath = os.path.join(dirinfo.base_path, 'Logs')

        if camera_name is not None and camera_poses is not None:
            # setup path
            pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)
            # dump
            _save_camera_poses_to_blend(
                name=camera_name,
                poses=camera_poses,
                filepath=os.path.join(logpath, basefilename + '.blend'))
 
        elif scn_idx is not None and view_idx is not None:
            # (if necessary) modify path and set up
            if on_error:
                logpath = _setup_logpath_on_error(logpath)
            pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)
            
            # file specs
            scn_frmt_w = int(ceil(log(self.config.dataset.scene_count, 10)))
            view_frmt_w = int(ceil(log(self.config.dataset.view_count, 10)))
            scn_str = f'_s{scn_idx:0{scn_frmt_w}}'
            view_str = f'_v{view_idx:0{view_frmt_w}}'

            # on error we save additional files
            if on_error:
                _save_data_on_error(
                    scn_str,
                    view_str,
                    dirinfo.images.rgb,
                    dirinfo.images.mask,
                    logpath,
                    self.objs)

            # finally save to blend
            filename = basefilename + scn_str + view_str + '.blend'
            filepath = os.path.join(logpath, filename)
            self.logger.info(f"Saving current scene/view to blender file {filepath} for debugging")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            
        else:
            pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)
            self.logger.info('Saving current active scene to blender for debugging')
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(logpath, basefilename + '.blend'))
