#!/usr/bin/env python

import bpy
import sys
from tempfile import NamedTemporaryFile


def activate_cuda_devices():
    """This function tries to activate all CUDA devices for rendering"""

    # get cycles preferences
    cycles = bpy.context.preferences.addons['cycles']
    prefs = cycles.preferences

    # set CUDA enabled, and activate all GPUs we have access to
    prefs.compute_device_type = 'CUDA'

    # determine if we have a GPU available
    cuda_available = False
    for d in prefs.get_devices()[0]:
        cuda_available = cuda_available or d.type == 'CUDA'

    # if we don't have a GPU available, then print a warning
    if not cuda_available:
        print("WW: No CUDA compute device available, will use CPU")
    else:
        device_set = False
        for d in prefs.devices:
            if d.type == 'CUDA':
                print(f"II: Using CUDA device 'f{d.name}' ({d.id})")
                d.use = True
            else:
                d.use = False

        for d in prefs.devices:
            print(d.name, d.use)

        # using the current scene, enable GPU Compute for rendering
        bpy.context.scene.cycles.device = 'GPU'


def get_output_path():
    """This function tries to determine the output path that the user specified
    (-o,--render-output). If nothing was specified, returns an empty string."""

    # get the path from argv
    argv = sys.argv
    try:
        index = argv.index('-o') + 1
    except:
        try:
            index = argv.index('--render-output') + 1
        except:
            index = -1

    if index == -1:
        return ''
    else:
        return argv[index]


def render_image():
    """This function first determines and sets the output path, then renders the image"""

    path = get_output_path()
    if path == '':
        path = NamedTemporaryFile(suffix='.png').name
        print(f"WW: No output path specified via '-o,--render-output'. Will store result to {path}")

    # set path
    bpy.context.scene.render.filepath = path
    # render
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    activate_cuda_devices()
    render_image()
