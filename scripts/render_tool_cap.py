#!/usr/bin/env python

# make amira_deep_vision packages available
import sys, os
import argparse
import numpy as np
import random
from math import log, ceil

def expandpath(path):
    return os.path.expandvars(os.path.expanduser(path))


def import_abr(paths=[]):
    """Import amira_blender_rendering.

    This might require setting up the system path. If both
    amira_blender_rendering and aps are installed, simply let path=[].
    """
    for p in paths:
        sys.path.append(expandpath(p))

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



def make_dataset(dirinfo, image_count, environment_textures):
    # filename setup
    format_width = int(ceil(log(image_count, 10)))
    base_filename = "{:0{width}d}".format(0, width=format_width)

    # setup blender CUDA rendering
    abr.blender_utils.activate_cuda_devices()

    # scene setup with a calibrated camera.
    # NOTE: at the moment there is a bug in abr.camera_utils:opencv_to_blender,
    #       which prevents us from actually using a calibrated camera. Still, we
    K = np.array([ 9.9801747708520452e+02, 0., 6.6049856967197002e+02, 0., 9.9264009290521165e+02, 3.6404286361152555e+02, 0., 0., 1. ]).reshape(3,3)
    width = 640
    height = 480
    scene = abr.scenes.SimpleToolCap(base_filename, dirinfo, K, width, height)

    # generate some images
    for i in range(image_count):
        # setup filename
        base_filename = "{:0{width}d}".format(i, width=format_width)
        scene.set_base_filename(base_filename)

        # set some environment texture
        filepath = expandpath(random.choice(environment_textures))
        scene.set_environment_texture(filepath)

        # actual rendering
        scene.randomize()
        scene.render()
        scene.postprocess()

    # finalize
    save_dataset_configuration(scene.dirinfo)


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def main():
    #
    parser = argparse.ArgumentParser(description='Render dataset for the "cap tool"', prog="blender -b -P " + __file__)
    parser.add_argument('--n', default=100, help='Number of images to render')
    parser.add_argument('--output-path', default='/tmp/BlenderRenderedObjects', help='Output path')
    parser.add_argument('--fixed-envtex', action='store_true', help='Use only a single environment texture')
    parser.add_argument('--envtex-path', default='$AMIRA_DATASETS/OpenImagesV4/Images', help='Path to environment textures. If --fixed-envtex is True, should point to file, otherwise should point to directory')
    parser.add_argument('--aps-path', default='~/dev/vision/amira_deep_vision', help='Path where AMIRA Perception Subsystem (aps) can be found')
    parser.add_argument('--abr-path', default='~/dev/vision/amira_blender_rendering/src', help='Path where amira_blender_rendering can be found')
    args = parser.parse_args(args=get_argv())

    # special imports
    import_abr([args.abr_path, args.aps_path])
    import_ro_static(args.aps_path)

    # set up of environment textures
    if args.fixed_envtex:
        environment_textures = [expandpath('~/gfx/assets/hdri/small_hangar_01_4k.hdr')]
        # environment_textures = [expandpath(args.envtex_path)]
    else:
        environment_textures = os.listdir(expandpath(args.envtex_path))
        environment_textures = [os.path.join(args.envtex_path, p) for p in environment_textures]

    # now ready to run
    dirinfo = ro_static.build_directory_info(args.output_path)
    make_dataset(dirinfo, args.n, environment_textures)


if __name__ == "__main__":
    main()

