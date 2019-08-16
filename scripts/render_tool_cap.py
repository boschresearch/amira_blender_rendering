#!/usr/bin/env python

# make amira_deep_vision packages available
import sys, os
import bpy
import numpy as np
import imageio
import argparse
from math import ceil, log
from mathutils import Vector, Euler
try:
    import ujson as json
except:
    import json


#
# ---- Configuration starts here
# TODO: move to a configuration file that we can directly import, and also
# change single environment texture to load arbitrary files
#


OUTPUT_PATH = '/tmp/BlenderRenderedObjects'
ENVIRONMENT_TEXTURE = '~/gfx/assets/hdri/small_hangar_01_4k.hdr'

N_IMAGES = 20



#
# ---- Configuration ends here
#

def import_abr(paths):
    """Import amira_blender_rendering and aps.

    This might require setting up the system path. If both packages are
    installed on your python path already, then let paths=[].
    """
    for p in paths:
        sys.path.append(os.path.expandvars(os.path.expanduser(p)))

    global abr
    import amira_blender_rendering as abr
    import amira_blender_rendering.blender_utils
    import amira_blender_rendering.scenes


def import_ro_static(aps_path):
    """Import the static methods from renderedobjects.

    We cannot import aps.data, because blender<->torch has some gflags issues that, at
    the moment, we cannot easily solve. That is, when running

        $ blender -c --python

    in a console, and then trying to import torch in the console

        >>> import torch

    you'll get an ERROR and blender quits. To circumvent this issue, we'll
    manually import the file that gives us directory information of
    renderedobjects within the following function. Fore more information, read
    the comment in the file that gets imported.
    """

    global ro_static

    APS_RENDERED_OBJECTS_STATIC_METHODS = 'aps/data/datasets/renderedobjects_static.py'
    import importlib
    try:
        fname = os.path.expanduser(os.path.join(
            aps_path,
            APS_RENDERED_OBJECTS_STATIC_METHODS))
        spec = importlib.util.spec_from_file_location('renderedobjects_static', fname)
        ro_static = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ro_static)
    except ImportError as e:
        raise RuntimeError(f"Could not import RenderedObjects' static methods")


def save_dataset_configuration(dirinfo):
    # TODO: save the dataset.cfg file
    pass


def make_dataset(dirinfo):
    # filename setup
    format_width = int(ceil(log(N_IMAGES, 10)))
    base_filename = "{:0{width}d}".format(0, width=format_width)

    # setup blender CUDA rendering
    abr.blender_utils.activate_cuda_devices()

    # scene instance
    scene = abr.scenes.SimpleToolCap(base_filename, dirinfo)

    # generate some images
    for i in range(N_IMAGES):

        # update filename
        base_filename = "{:0{width}d}".format(i, width=format_width)
        scene.set_base_filename(base_filename)

        scene.randomize()

        # postprocessing
        scene.render()
        scene.postprocess()

    # finalize
    save_dataset_configuration(scene.dirinfo)


def main():
    # import things
    APS_PATH = '~/dev/vision/amira_deep_vision'
    ABR_PATH = '~/dev/vision/amira_blender_rendering/src'

    # special imports
    paths = [ABR_PATH, APS_PATH]
    import_abr(paths)
    import_ro_static(APS_PATH)


    # now ready to run
    dirinfo = ro_static.build_directory_info(OUTPUT_PATH)
    make_dataset(dirinfo)


if __name__ == "__main__":
    main()
