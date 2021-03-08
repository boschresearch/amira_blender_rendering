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
import bpy
from amira_blender_rendering.utils.logging import get_logger


class CompositorNodesOutputRenderedObjects():
    """This class contains the setup of compositor nodes that is required for
    the RenderedObjects dataset. Using this class will set up FileOutput and ID
    Mask nodes such that we not only get the rendered image, but also Depth
    information (in OpenEXR format), image masks for each object of interest, as
    well as a backdrop (mask excluding any object of interest."""

    def __init__(self):
        super(CompositorNodesOutputRenderedObjects, self).__init__()

        self.dirinfo = None
        self.sockets = dict()
        self.nodes = dict()
        self.base_filename = ''
        # list of objects to handle and corresponding unique name.
        # These are used to setup socket and outputfiles
        self.objs = []
        self.scene = None

    def __extract_pathspec(self):
        """Extract relevant paths from self.dirinfo.

        In blender we operate with relative paths, whereas in amira_perception we
        currently use absolute paths. This should be changed to use some common
        dataset description format (but please no XML garbage).

        Args:
            dirinfo (DynamicStruct): directory information for the rendered_objects
                dataset. See amira_perception for more details
        """

        self.path_base = self.dirinfo.images.base_path

        prefix = self.dirinfo.images.base_path
        self.path_rgb = self.dirinfo.images.rgb[len(prefix) + 1:]
        self.path_rgb = os.path.join(self.path_rgb, '')

        self.path_range = self.dirinfo.images.range[len(prefix) + 1:]
        self.path_range = os.path.join(self.path_range, '')

        self.path_mask = self.dirinfo.images.mask[len(prefix) + 1:]
        self.path_mask = os.path.join(self.path_mask, '')

        self.path_backdrop = self.dirinfo.images.backdrop[len(prefix) + 1:]
        self.path_backdrop = os.path.join(self.path_backdrop, '')

    def __update_node_paths(self):
        """This function will update all base-path knowledge in the node editor"""

        # get node tree
        tree = bpy.context.scene.node_tree
        nodes = tree.nodes

        n_output_file = nodes['RenderObjectsFileOutputNode']
        n_output_file.base_path = self.path_base

    # NOTE: setup was split into setup_nodes and setup_pathspec
    def setup_nodes(self, objs: list, scene: bpy.types.Scene = bpy.context.scene, **kw):
        """Setup all compositor nodes that are required for exporting to the
        RenderObjects dataset format.

        Args:
            objs (list): list of dictionaries with objects (for which a mask needs to be generated) info.
                Minimal info needed:
                [{
                    'id_mask'(str): string with unique id for mask generation
                    'bpy'(bpy.types.Object): actual bpy object
                    ...
                }
                ...
                ]
            scene (bpy.types.Scene): blender scene on which to operate

        Returns:
            dict containing all file output sockets. This dict can be passed to
            update_compositor_nodes_rendered_objects in case of dynamic filename changes.
        """

        # prevent blender from adding file extensions
        if self.scene is None:
            self.scene = bpy.context.scene
        self.scene.render.use_file_extension = False

        # enable nodes, and enable object index pass (required for mask)
        self.scene.use_nodes = True
        self.scene.view_layers['View Layer'].use_pass_object_index = True
        tree = self.scene.node_tree
        nodes = tree.nodes
        n_render_layers = nodes['Render Layers']

        # add file output node and setup format (16bit RGB without alpha channel)
        n_output_file = nodes.new('CompositorNodeOutputFile')
        n_output_file.name = 'RenderObjectsFileOutputNode'
        # n_output_file.base_path = self.path_base

        # the following format will be used for all sockets, except when setting a
        # socket's use_node_format to False (see range map as example)
        n_output_file.format.file_format = 'PNG'
        n_output_file.format.color_mode = 'RGB'
        n_output_file.format.color_depth = str(kw.get('color_depth', 16))

        # setup sockets/slots. First is RGBA Image by default
        s_render = n_output_file.file_slots[0]
        s_render.use_node_format = True
        tree.links.new(n_render_layers.outputs['Image'], n_output_file.inputs['Image'])
        self.sockets['s_render'] = s_render

        # add all aditional file slots, e.g. depth map, image masks, backdrops, etc.
        # NOTE: blender Depth map is indeed a range map since it uses a perfect pinhole camera.
        #       That is, the map is not rectified yet.
        n_output_file.file_slots.new('Depth')
        s_depth_map = n_output_file.file_slots['Depth']
        s_depth_map.use_node_format = False
        s_depth_map.format.file_format = 'OPEN_EXR'
        s_depth_map.format.use_zbuffer = True
        tree.links.new(n_render_layers.outputs['Depth'], n_output_file.inputs['Depth'])
        self.sockets['s_depth_map'] = s_depth_map

        # backdrop setup (mask without any object)
        n_id_mask = nodes.new('CompositorNodeIDMask')
        n_id_mask.index = 0
        n_id_mask.use_antialiasing = True
        tree.links.new(n_render_layers.outputs['IndexOB'], n_id_mask.inputs['ID value'])

        mask_name = "Backdrop"
        n_output_file.file_slots.new(mask_name)
        s_obj_mask = n_output_file.file_slots[mask_name]
        s_obj_mask.use_node_format = True
        tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])
        self.sockets['s_backdrop'] = s_obj_mask

        # add nodes and sockets for all masks
        for i, obj in enumerate(objs):
            # setup object (this will change the pass index). The pass_index must be > 0 for the mask to work.
            obj['bpy'].pass_index = i + 1337

            # mask
            n_id_mask = nodes.new('CompositorNodeIDMask')
            n_id_mask.index = obj['bpy'].pass_index
            n_id_mask.use_antialiasing = True
            tree.links.new(n_render_layers.outputs['IndexOB'], n_id_mask.inputs['ID value'])

            # new socket in file output
            mask_name = f"Mask{i:03}"
            n_output_file.file_slots.new(mask_name)
            s_obj_mask = n_output_file.file_slots[mask_name]
            s_obj_mask.use_node_format = True
            tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])
            self.sockets[f"s_obj_mask{obj['id_mask']}"] = s_obj_mask

        return self.sockets

    # NOTE: this function was called update, but was renamed
    def setup_pathspec(self, dirinfo, render_filename: str, objs: dict, scene: bpy.types.Scene = bpy.context.scene):
        """Update the compositor nodes with new filenames and base directory information

        Args:
            dirinfo: directory information struct of RenderedObject datasets
            render_filename (str): new filename (without file extension)
            objs (list): list of dictionaries with objects (for which a mask needs to be generated) info.
                Minimal info needed:
                [{
                    'id_mask'(str): string with unique id for mask generation
                    'bpy'(bpy.types.Object): actual bpy object
                    ...
                }
                ...
                ]
            scene (bpy.types.Scene): blender scene on which to operate

        Returns:
            The sockets dictionary
        """

        # TODO: check if scene is different from before, because then we have to
        # setup the entire node tree for this scene again (or raise an
        # exception)

        # set all members and compute path related specifications
        self.dirinfo = dirinfo
        self.base_filename = render_filename
        self.objs = objs
        self.scene = scene
        # extract paths and update in node
        self.__extract_pathspec()
        self.__update_node_paths()

        self.sockets['s_render'].path = os.path.join(self.path_rgb, f'{self.base_filename}.png####')
        self.sockets['s_depth_map'].path = os.path.join(self.path_range, f'{self.base_filename}.exr####')
        self.sockets['s_backdrop'].path = os.path.join(self.path_backdrop, f'{self.base_filename}.png####')
        # obj_names are used to setup corresponding output files for masks
        for obj in objs:
            self.sockets[f's_obj_mask{obj["id_mask"]}'].path = os.path.join(
                self.path_mask, f'{self.base_filename}{obj["id_mask"]}.png####')
        return self.sockets

    def postprocess(self):
        """Postprocessing: Repair all filenames and make mask filenames accessible to
        each corresponding object.

        Blender adds the frame number in filenames. It is not possible to change
        this behavior, even in file output nodes in the compositor. The
        workaround that we use here is to store everything as
        desired-filename.ext0001, and then, within this function, rename these
        files to desired-filename.ext.
        """

        # TODO: all TODO items from the _update function above apply!

        # turn the frame number into a string. given the update function,
        # blender will write files with the framenumber as four trailing digits
        frame_number = int(bpy.context.scene.frame_current)
        frame_number_str = f"{frame_number:04}"

        # get file names
        self.fname_render = os.path.join(self.dirinfo.images.rgb, f'{self.base_filename}.png{frame_number_str}')
        self.fname_range = os.path.join(self.dirinfo.images.range, f'{self.base_filename}.exr{frame_number_str}')
        self.fname_backdrop = os.path.join(
            self.dirinfo.images.base_path, 'backdrop', f'{self.base_filename}.png{frame_number_str}')
        for f in (self.fname_render, self.fname_range, self.fname_backdrop):
            if not os.path.exists(f):
                get_logger().error(f"File {f} expected, but does not exist")
            else:
                os.rename(f, f[:-4])

        # store mask filename for other users that currently need the mask
        for obj in self.objs:
            fname_mask = os.path.join(
                self.dirinfo.images.mask, f'{self.base_filename}{obj["id_mask"]}.png{frame_number_str}')
            os.rename(fname_mask, fname_mask[:-4])
            # store name of mask file into dict of corresponding obj
            # TODO: not sure is good to modify the dict but I like more than the list of fname_masks
            obj['fname_mask'] = fname_mask[:-4]
