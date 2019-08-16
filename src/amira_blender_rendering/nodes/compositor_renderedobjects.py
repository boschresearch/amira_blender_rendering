#!/usr/bin/env python

import os
from typing import List
import bpy


class CompositorNodesOutputRenderedObject():
    """This class contains the setup of compositor nodes that is required for
    the RenderedObjects dataset. Using this class will set up FileOutput and ID
    Mask nodes such that we not only get the rendered image, but also Depth
    information (in OpenEXR format), image masks for each object of interest, as
    well as a backdrop (mask excluding any object of interest."""



    def __init__(self):
        super(CompositorNodesOutputRenderedObject, self).__init__()

        self.dirinfo = None
        self.sockets = dict()
        self.base_filename = ''
        self.objs = []
        self.scene = None


    def __extract_pathspec(self):
        """Extract relevant paths from self.dirinfo.

        In blender we operate with relative paths, whereas in amira_deep_vision we
        currently use absolute paths. This should be changed to use some common
        dataset description format (but please no XML garbage).

        Args:
            dirinfo (DynamicStruct): directory information for the rendered_objects
                dataset. See amira_deep_vision for more details

        Returns:
            5-tuple: base path, followed by relative paths for constant light, random light,
            depth, and mask.
        """

        self.path_base = self.dirinfo.images.base_path

        prefix = self.dirinfo.images.base_path
        self.path_img_const = self.dirinfo.images.const[len(prefix) + 1:]
        self.path_img_const = os.path.join(self.path_img_const, '')

        self.path_img_rand = self.dirinfo.images.random[len(prefix) + 1:]
        self.path_img_rand = os.path.join(self.path_img_rand, '')

        self.path_depth = self.dirinfo.images.depth[len(prefix) + 1:]
        self.path_depth = os.path.join(self.path_depth, '')

        self.path_mask = self.dirinfo.images.mask[len(prefix) + 1:]
        self.path_mask = os.path.join(self.path_mask, '')

        return self.path_base, self.path_img_const, self.path_img_rand, self.path_depth, self.path_mask


    def setup(self,
            dirinfo,
            filename,
            objs : List[bpy.types.Object],
            scene: bpy.types.Scene = bpy.context.scene):
        """Setup all compositor nodes that are required for exporting to the
        RenderObjects dataset format.

        Args:
            dirinfo (DynamicStruct): directory information for the rendered_objects
                dataset. See amira_deep_vision for more details
            filename (str): Filename of output (without file extension)
            objs (List[bpy.types.Object]): list of objects for which to compute an output mask
            scene (bpy.types.Scene): blender scene on which to operate

        Returns:
            dict containing all file output sockets. This dict can be passed to
            update_compositor_nodes_rendered_objects in case of dynamic filename changes.
        """

        # TODO: at the moment we get the dirinfo passed in here instead of just
        # importing RenderedObjects from amira_deep_vision. This is because of
        # the torch-import issue that is documented in the amira_deep_vision
        # repository. As soon as this is fixed, and either the amira_deep_vision
        # repository is on sys.path, or the aps package (amira perception
        # subsystem) is installed, we can simpy import it.
        self.dirinfo = dirinfo
        self.base_filename = filename
        self.objs = objs
        self.scene = scene
        self.__extract_pathspec()

        # prevent blender from adding file extensions
        self.scene.render.use_file_extension = False

        # enable nodes, and enable object index pass (required for mask)
        self.scene.use_nodes = True
        self.scene.view_layers['View Layer'].use_pass_object_index = True
        tree = self.scene.node_tree
        nodes = tree.nodes
        n_render_layers = nodes['Render Layers']

        # add file output node and setup format (16bit RGB without alpha channel)
        n_output_file = nodes.new('CompositorNodeOutputFile')
        n_output_file.base_path = self.path_base

        # the following format will be used for all sockets, except when setting a
        # socket's use_node_format to False (see depth map as example)
        n_output_file.format.file_format = 'PNG'
        n_output_file.format.color_mode = 'RGB'
        n_output_file.format.color_depth = '16'

        # setup sockets/slots. First is RGBA Image by default
        s_render = n_output_file.file_slots[0]
        s_render.use_node_format = True
        tree.links.new(n_render_layers.outputs['Image'], n_output_file.inputs['Image'])
        self.sockets['s_render'] = s_render

        # add all aditional file slots, e.g. depth map, image masks, backdrops, etc.
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

        mask_name = f"Backdrop"
        n_output_file.file_slots.new(mask_name)
        s_obj_mask = n_output_file.file_slots[mask_name]
        s_obj_mask.use_node_format = True
        tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])
        self.sockets['s_backdrop'] = s_obj_mask


        # add nodes and sockets for all masks
        for i, obj in enumerate(objs):
            # setup object (this will change the pass index). The pass_index must be > 0 for the mask to work.
            obj.pass_index = i+1

            # mask
            n_id_mask = nodes.new('CompositorNodeIDMask')
            n_id_mask.index = obj.pass_index
            n_id_mask.use_antialiasing = True
            tree.links.new(n_render_layers.outputs['IndexOB'], n_id_mask.inputs['ID value'])

            # new socket in file output
            mask_name = f"Mask{i:03}"
            n_output_file.file_slots.new(mask_name)
            s_obj_mask = n_output_file.file_slots[mask_name]
            s_obj_mask.use_node_format = True
            tree.links.new(n_id_mask.outputs['Alpha'], n_output_file.inputs[mask_name])
            self.sockets[f"s_obj_mask{i}"] = s_obj_mask

        # set the paths of all sockets
        self.update(dirinfo, self.base_filename, objs)
        return self.sockets


    def update(self,
            dirinfo,
            filename: str,
            objs: List[bpy.types.Object],
            scene: bpy.types.Scene = bpy.context.scene):
        """Update the compositor nodes with a new filename.

        Args:
            dirinfo: directory information struct of RenderedObject datasets
            filename (str): new filename (without file extension)
            objs (List[bpy.types.Object]): list of objects for which a filename
                needs to be generated. Note that the list should have the same order of
                objects as used during setup_compositor_nodes_rendered_objects.

        Returns:
            The sockets dictionary
        """

        # TODO: check if scene is different from before, because then we have to
        # setup the entire node tree for this scene again (or raise an
        # exception)

        # set all members and compute path related specifications
        self.dirinfo = dirinfo
        self.base_filename = filename
        self.objs = objs
        self.scene = scene
        self.__extract_pathspec()

        # TODO: backdrop is currently not part of the RenderedObjects specification.
        #       Should be included.

        # TODO: this will not work for >1 objects, because they will simply
        #       overwrite the output file. The RenderedObjects dataset specification
        #       cannot handle multiple objects at the moment. As soon as this is
        #       changed, we can also properly set up multiple output sockets.
        self.sockets['s_render'].path    = os.path.join(self.path_img_const,   f'{self.base_filename}.png####')
        self.sockets['s_depth_map'].path = os.path.join(self.path_depth,       f'{self.base_filename}.exr####')
        self.sockets['s_backdrop'].path  = os.path.join('backdrop',            f'{self.base_filename}.png####')
        for i in range(len(objs)):
            self.sockets[f"s_obj_mask{i}"].path = os.path.join(self.path_mask, f'{self.base_filename}.png####')
        return self.sockets


    def postprocess(self):
        """Postprocessing: Repair all filenames.

        Blender adds the frame number in filenames. It is not possible to change
        this behavior, even in file output nodes in the compsitor. The
        workaround that we use here is to store everything as
        desired-filename.ext0001, and then, within this function, rename these
        files to desired-filename.ext.
        """

        # TODO: all TODO items from the _update function above apply!

        self.fname_render   = os.path.join(self.dirinfo.images.const,                 f'{self.base_filename}.png0001')
        self.fname_depth    = os.path.join(self.dirinfo.images.depth,                 f'{self.base_filename}.exr0001')
        self.fname_backdrop = os.path.join(self.dirinfo.images.base_path, 'backdrop', f'{self.base_filename}.png0001')
        for f in (self.fname_render, self.fname_depth, self.fname_backdrop):
            os.rename(f, f[:-4])

        # store mask filename for other users that currently need the mask
        self.fname_masks = []
        for i in range(len(self.objs)):
            fname_mask = os.path.join(self.dirinfo.images.mask,                  f'{self.base_filename}.png0001')
            os.rename(fname_mask, fname_mask[:-4])
            self.fname_masks.append(fname_mask[:-4])
