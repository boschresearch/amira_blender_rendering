#!/usr/bin/env python

import bpy


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

        # enable GPU compute devices for the current scene
        bpy.context.scene.cycles.device = 'GPU'

def render_image():
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    activate_cuda_devices()
    render_image()
