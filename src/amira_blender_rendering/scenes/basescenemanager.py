#!/usr/bin/env python

import os
import bpy
from amira_blender_rendering.utils import blender as blnd
from amira_blender_rendering.utils.logging import get_logger

class BaseSceneManager():
    """Class for arbitrary scenes that should be set up for rendering data.

    This class should act as an an entry point for arbitrary scenarios.
    """

    def __init__(self):
        super(BaseSceneManager, self).__init__()
        self.init_default_blender_config()
        self.logger = get_logger()

    def init_default_blender_config(self):
        """This function is used to setup blender into a known configuration,
        such as which unit system to use."""

        # unit system
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.length_unit = 'METERS'
        bpy.context.scene.unit_settings.scale_length = 1.0

    def reset(self):
        blnd.clear_all_objects()
        blnd.clear_orphaned_materials()

    def set_environment_texture(self, filepath):
        """Set a specific environment texture for the scene"""

        # check if path exists or not
        if not os.path.exists(filepath):
            self.logger.error(f"Path {filepath} to environment texture does not exist.")
            return

        # add new environment texture node if required
        tree = bpy.context.scene.world.node_tree
        nodes = tree.nodes
        if 'Environment Texture' not in nodes:
            nodes.new('ShaderNodeTexEnvironment')
        n_envtex = nodes['Environment Texture']

        # retrieve image object and set
        img = blnd.load_img(filepath)
        n_envtex.image = img

        # setup link (doesn't matter if already exists, won't duplicate)
        tree.links.new(n_envtex.outputs['Color'], nodes['Background'].inputs['Color'])


# TODO: this should become a UnitTest
if __name__ == "__main__":
    mgr = BaseSceneManager()
    mgr.set_environment_texture(os.path.expanduser('~/gfx/assets/hdri/machine_shop_02_4k.hdr'))
