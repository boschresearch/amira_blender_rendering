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

from amira_blender_rendering.datastructures import Configuration

class BaseConfiguration(Configuration):
    """Basic configuration for any dataset."""

    def __init__(self):
        super(BaseConfiguration, self).__init__()

        # general dataset configuration.
        self.add_param('dataset.image_count', 1, 'Number of images to generate')
        self.add_param('dataset.base_path', '', 'Path to storage directory')
        self.add_param('dataset.scene_type', '', 'Scene type')

        # camera configuration
        self.add_param('camera_info.name', 'Pinhole Camera', 'Name for the camera')
        self.add_param('camera_info.model', 'pinhole', 'Camera model type')
        self.add_param('camera_info.width', 640, 'Rendered image resolution (pixel) along x (width)')
        self.add_param('camera_info.height', 480, 'Rendered image resolution (pixel) along y (height)')
        self.add_param('camera_info.zeroing', [0.0, 0.0, 0.0], 'Default camera zeroing rotation in degrees')
        self.add_param('camera_info.intrinsic', [], 'camera intrinsics fx, fy, cx, cy, possible altered via blender during runtime', special='maybe_list')
        # self.add_param('camera_info.original_intrinsic', [], 'Camera intrinsics that were passed originaly as camera_info.intrinsic', special='maybe_list')

        # render configuration
        self.add_param('render_setup.backend', 'blender-cycles', 'Render backend. Blender only one supported')
        self.add_param('render_setup.integrator', 'BRANCHED_PATH', 'Integrator used during path tracing. Either of PATH, BRANCHED_PATH')
        self.add_param('render_setup.denoising', True, 'Use denoising algorithms during rendering')
        self.add_param('render_setup.samples', 128, 'Samples to use during rendering')

