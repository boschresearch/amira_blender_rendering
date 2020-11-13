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

"""
This file contains classes and prototypes that are shared with amira_perception.
In particular, it specifies how rendering results should be stored.
"""

import os
import pathlib
import bpy
from math import ceil, log
from amira_blender_rendering.datastructures import filter_state_keys
from amira_blender_rendering.math.geometry import rotation_matrix_to_quaternion
from amira_blender_rendering.utils.logging import get_logger
import amira_blender_rendering.utils.blender as blnd

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
    rgbname = scn_str[1:] + view_str + f'.png'
    srcpath = os.path.join(rgb_base_path, rgbname)
    dstpath = os.path.join(logpath, rgbname)
    copyfile(srcpath, dstpath)
    # copy masks
    for obj in objs:
        maskname = scn_str[1:] + view_str + f'{obj["id_mask"]}.png'
        srcpath = os.path.join(mask_base_path, maskname)
        dstpath = os.path.join(logpath, maskname)
        copyfile(srcpath, dstpath)


def _save_camera_locations_to_blend(name: str, locations: list, filepath: str):
    """Save a given list of camera locations to blend.

    Args:
        name(str): camera name as in the prescribed blender file
        locations(list): list of camera locations
        filepath(str): path where .blend file is saved
    """
    if name is None or locations is None:
        logger.warn('Either given camera name or locations are None. To dump both must be given. Skipping')
        return

    # create and link temporary collection
    tmp_cam_coll = bpy.data.collections.new('TemporaryCameras')
    bpy.context.scene.collection.children.link(tmp_cam_coll)

    tmp_cameras = []
    for location in locations:
        blnd.select_object(name)
        bpy.ops.object.duplicate()
        # TODO: remove from original collection to avoid name clutter in .blend
        tmp_cam_obj = bpy.context.object
        tmp_cam_obj.location = location
        tmp_cam_coll.objects.link(tmp_cam_obj)
        tmp_cameras.append(tmp_cam_obj)
    bpy.context.evaluated_depsgraph_get().update()

    logger.info(f"Saving camera locations to blender file {filepath} for debugging")
    bpy.ops.wm.save_as_mainfile(filepath=filepath)

    # clear objects and collection
    bpy.ops.object.select_all(action='DESELECT')
    for tmp_cam in tmp_cameras:
        bpy.data.objects.remove(tmp_cam)
    bpy.data.collections.remove(tmp_cam_coll)


# TODO: derive scenes in abr.scenes from this class
class ABRScene():
    """interface of functions that each sccene needs to adhere to"""
    def __init__(self):
        pass

    def dump_config(self):
        raise NotImplementedError()

    def generate_dataset(self):
        raise NotImplementedError()

    def generate_viewsphere_dataset(self):
        raise NotImplementedError()

    def teardown():
        raise NotImplementedError()

    def save_to_blend(self, dirinfo, **kw):
        """
        Save debug data to .blend files

        The behavior of the method depends on its keywords input arguments.
        In particular:
            - with no optional args: it dump the current active scene to .blend in ActiveCamera/Logs
                                    where ActiveCamera identify the directory where data, i.e.,
                                    Images and Annotations, for the currently active camera are stored.
            - with camera_name and camera_locations: the active camera is duplicated and placed in all
                                                    given locations.
                                                    Use this behavior to check whether generated locations
                                                    are valid.
            - with view_index and scene_index: the current active scene is logged to .blend
                                                following ABR base filenaming convention
                - if additionally on_error == True: data are logged to a separate timestamped subdirectory
                                                    (together with additional data) to avoid data overwrite

        NOTE: camera_name and camera_locations have priority. That is, if given, other kwargs are not considered.

        Args:
            dirinfo(dict-like/Configuration): struct with information about dataset filesystem

        Kwargs Args:
            camera_name(str): name for active camera, as appears in the active scene
            camera_locations(list): list containing multiple camera locations
            scene_index(int): index of static scene being rendered
            view_index(int): index of current view being rendered
            on_error(bool): if True, assume an error has been raised and additional data are logged
        """
        # extract args
        basefilename = kw.get('basefilename', 'debug')
        
        camera_name = kw.get('camera_name', None)
        camera_locations = kw.get('camera_locations', None)

        scn_idx = kw.get('scene_index', None)
        view_idx = kw.get('view_index', None)
        on_error = kw.get('on_error', False)

        # extract and  (if necessary) create log directory
        logpath = os.path.join(dirinfo.base_path, 'Logs')

        if camera_name is not None and camera_locations is not None:
            # setup path
            pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)
            # dump
            _save_camera_locations_to_blend(
                name=camera_name,
                locations=camera_locations,
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
            filename = basefilename + scn_str + view_str + f'.blend'
            filepath = os.path.join(logpath, filename)
            logger.info(f"Saving current scene/view to blender file {filepath} for debugging")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            
        else:
            pathlib.Path(logpath).mkdir(parents=True, exist_ok=True)
            logger.info('Saving current active scene to blender for debugging')
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(logpath, basefilename + '.blend'))



# NOTE: the functions and classes below were taken from amira_perception. Make
#       sure to keep in sync as long as we don't have a core library that is
#       restricted to such functionality
#
# NOTE: unnecessary classes/methods have been pruned


class ResultsCollection:
    """Base class to handle detection results and IO of results"""

    def __init__(self):
        """Class constructor"""
        self._list = list()

    def add_result(self, r):
        """add single result"""
        self._list.append(r)

    def add_results(self, res):
        """add results from a list"""
        for r in res:
            self.add_result(r)

    def get_results(self):
        return self._list

    def get_result(self, idx):
        return self._list[idx]

    def __iter__(self):
        for el in self._list:
            yield el

    def __len__(self):
        return len(self._list)

    def state_dict(self, retain_keys: list = None):
        """Make results serializable (for writing out). Filter result keys if desired.

        Opt Args:
            retain_keys([]): list of keys to retain when converting to state_dict
        """
        if retain_keys is None:
            retain_keys = []
        return [r.state_dict(retain_keys) for r in self]


class PoseRenderResult:

    def __init__(self, object_class_name, object_class_id, object_name, object_id,
                 rgb_const, rgb_random, depth, mask,
                 rotation, translation,
                 corners2d, corners3d, aabb, oobb,
                 dense_features=None,
                 mask_name='',
                 visible=None,
                 camera_rotation=None,
                 camera_translation=None):
        """Initialize struct to store the result of rendering synthetic data

        Args:
            object_class_name(str): name of rendered class (type of object)
            object_class_id(int): id for class (if any). To distinguish among different model classes
            object_name(str): object specific name (instance name)
            object_id(int): object specific id (if any). To distinguish among different instances
            rgb_const: image with constant light position across generated samples
            rgb_random: image with a random light position
            depth: depth image
            mask: stencil that masks the object
            rotation(np.array(3,3) or np.array(4): rotation embedded as 3x3 rotation matrix or (4,) quaternion (WXYZ).
                Internally, we store rotation as quaternion only.
            translation(np.array(3,)): translation vector
            corners2d: 2D bbox in image space (image space aligned, not object-oriented!.) (top-left, bottom-right)
            corners2d: object-oriented bbox projected to image space (first element is the centroid)
            aabb: axis aligned bounding box around object (this is in model-coordinates before model-world transform)
            oobb: object-oriented bounding box in 3D world coordinates (this is after view-rotation)
        
        Optional Args:
            dense_features: optional dense feature representation of the surface
            mask_name(str): optional mask name to indetify correct mask in multi object scenarios. Default: ''
            visible(bool): optional visibility flag
            camera_rotation(np.array): camera extrinsic rotation (world coordinate)
            camera_translation(np.array): camera extrinsic translation (world coordinate)
        """
        self.object_class_name = object_class_name
        self.object_class_id = object_class_id
        self.object_name = object_name
        self.object_id = object_id
        self.rgb_const = rgb_const
        self.rgb_random = rgb_random
        self.depth = depth
        self.mask = mask
        self.dense_features = dense_features
        self.q = try_rotation_to_quaternion(rotation)  # WXYZ
        self.t = translation
        self.corners2d = corners2d
        self.corners3d = corners3d
        self.oobb = oobb
        self.aabb = aabb
        self.mask_name = mask_name
        self.visible = visible
        self.q_cam = try_rotation_to_quaternion(camera_rotation)  # WXYZ
        self.t_cam = camera_translation

    def state_dict(self, retain_keys: list = None):
        data = {
            "object_class_name": self.object_class_name,
            "object_class_id": self.object_class_id,
            "object_name": self.object_name,
            "object_id": self.object_id,
            "mask_name": self.mask_name,
            "visible": self.visible,
            "pose": {
                "q": try_to_list(self.q),
                "t": try_to_list(self.t),
            },
            "bbox": {
                "corners2d": try_to_list(self.corners2d),
                "corners3d": try_to_list(self.corners3d),
                "aabb": try_to_list(self.aabb),
                "oobb": try_to_list(self.oobb)
            },
            "camera_pose": {
                "q": try_to_list(self.q_cam),
                "t": try_to_list(self.t_cam)
            }
        }
        if self.dense_features is not None:
            data['dense_features'] = try_to_list(self.dense_features)
        
        return filter_state_keys(data, retain_keys)


def try_to_list(in_array):
    return in_array.tolist() if in_array is not None else None


def try_rotation_to_quaternion(rotation):
    """
    Try to convert given rotation to quaternion WXYZ

    Args:
        rotation: matrix or quaternion or None
    
    Returns:
        quaternion or None
    """
    if rotation is None:
        q = None
    else:
        if rotation.shape == (3, 3):
            q = rotation_matrix_to_quaternion(rotation)
        else:
            q = rotation.flatten()
            if q.shape != (4,):
                q = None
                raise ValueError('Rotation must be either a (3,3) matrix or a (4,) quaternion (WXYZ)')
    return q
