#!/usr/bin/env python

"""This script can be used to generate RenderedObjects datasets of the cap tool.

The script must be run in blender, for instance from the command line using:

    $ blender -b -P scripts/render_dataset_RenderedObjects.py

The script accepts several additional arguments. The most important is the path
to the render configuration file, which defaults to 'config/render_toolcap.cfg'.
The script also needs to find amira_blender_rendering, as well as aps (AMIRA
Perception Subsystem) and foundry (also part of amira_deep_vision). Path to
their parent-folders can be passed along as command-line arguments via the
--arb-path and --aps-path flags.s

Example:

    $ blender -b -P scripts/render_dataset_RenderedObjects.py -- --arb-path ~/amira/amira_blender_rendering --aps-path ~/amira/amira_deep_vision

Note that paths will be expanded, i.e. variables such as $AMIRA_DATASETS or ~
will be turned into their proper values.

"""


# make amira_deep_vision packages available
import bpy
import sys, os
import argparse, configparser
import numpy as np
import random
from math import log, ceil


def expandpath(path):
    return os.path.expandvars(os.path.expanduser(path))


def import_aps(path=None):
    """Import the AMIRA Perception Subsystem."""
    if path is not None:
        sys.path.append(expandpath(path))

    global aps
    global foundry
    global RenderedObjects

    import aps
    import aps.core
    from aps.data.datasets.renderedobjects import RenderedObjects

    from aps.data.utils.viewspheresampler import ViewSampler

    import foundry
    import foundry.utils


def import_abr(path=None):
    """Import amira_blender_rendering."""
    if path is not None:
        sys.path.append(expandpath(path))

    global abr
    import amira_blender_rendering as abr
    import amira_blender_rendering.blender_utils
    import amira_blender_rendering.scenes


def get_environment_textures(cfg):
    """Determine if the user wants to set specific environment texture, or
    randomly select from a directory"""

    environment_textures = expandpath(cfg['render_setup']['environment_texture'])
    if os.path.isdir(environment_textures):
        files = os.listdir(environment_textures)
        environment_textures = [os.path.join(environment_textures, f) for f in files]
    else:
        environment_textures = [environment_textures]

    return environment_textures


def get_scene_type(type_str : str):
    """Get the (literal) type of a scene given a string.

    Essentially, this is what literal_cast does in C++, but for user-defined
    types.

    Args:
        type_str(str): type-string of a scene without module-prefix

    Returns:
        type corresponding to type_str
    """
    # specify mapping from str -> type to get the scene
    # TODO: this might be too simple at the moment, because some scenes might
    #       require more arguments. But we could think about passing along a
    #       Configuration object, similar to whats happening in aps
    scene_types = {
        'SimpleToolCap': abr.scenes.SimpleToolCap,
        'SimpleLetterB': abr.scenes.SimpleLetterB,
    }
    if type_str not in scene_types:
        known_types = str([k for k in scene_types.keys()])[1:-1]
        raise Exception(f"Scene type {type_str} not known. Known types: {known_types}. Note that scene types are case sensitive.")
    return scene_types[type_str]


def setup_renderer(cfg):
    """Setup blender CUDA rendering, and specify number of samples per pixel to
    use during rendering. If the setting render_setup.samples is not set in the
    configuration, the function defaults to 128 samples per image."""
    abr.blender_utils.activate_cuda_devices()
    n_samples = int(cfg['render_setup']['samples']) if 'samples' in cfg['render_setup'] else 128
    bpy.context.scene.cycles.samples = n_samples


def generate_dataset(cfg, dirinfo):
    """Generate images and metadata for a dataset, specified by cfg and dirinfo"""

    setup_renderer(cfg)

    image_count = int(cfg['dataset']['image_count'])
    environment_textures = get_environment_textures(cfg)

    # filename setup
    format_width = int(ceil(log(image_count, 10)))
    base_filename = "{:0{width}d}".format(0, width=format_width)

    # scene setup with a calibrated camera.
    # NOTE: at the moment there is a bug in abr.camera_utils:opencv_to_blender,
    #       which prevents us from actually using a calibrated camera. Still, we
    #       pass it along here because at some point, we might actually have
    #       working implementation ;)
    width  = int(cfg['camera_info']['width'])
    height = int(cfg['camera_info']['height'])
    K = None
    if 'K' in cfg['camera_info']:
        K = np.fromstring(cfg['camera_info']['K'], sep=',')

    # instantiate scene
    scene_type = get_scene_type(cfg['render_setup']['scene_type'])
    scene = scene_type(base_filename, dirinfo, K, width, height)

    # generate images
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


def generate_viewsphere(cfg, dirinfo):
    """Generate images and metadata for a view sphere, specified by cfg and dirinfo
    
    Args:
        cfg()
        dirinfo():
    """

    setup_renderer(cfg)

    # sample views
    sampler = ViewSampler()
    rototranslations = sampler.viewsphere_rototranslations(
        int(cfg['viewsphere']['min_num_views']),
        float(cfg['viewsphere']['radius']),
        int(cfg['viewsphere']['num_inplane_rotations'])
    )
    
    # get textures
    environment_textures = get_environment_textures(cfg)

    # compute image count and ovewrite cfg to be dumped
    image_count = len(rototranslations)
    cfg['dataset']['image_count'] = str(image_count)

    # filename setup
    format_width = int(ceil(log(image_count, 10)))
    base_filename = "{:0{width}d}".format(0, width=format_width)

    # scene setup with a calibrated camera.
    # NOTE: at the moment there is a bug in abr.camera_utils:opencv_to_blender,
    #       which prevents us from actually using a calibrated camera. Still, we
    #       pass it along here because at some point, we might actually have
    #       working implementation ;)
    width  = int(cfg['camera_info']['width'])
    height = int(cfg['camera_info']['height'])
    K = None
    if 'K' in cfg['camera_info']:
        K = np.fromstring(cfg['camera_info']['K'], sep=',')

    # instantiate scene
    scene_type = get_scene_type(cfg['render_setup']['scene_type'])
    scene = scene_type(base_filename, dirinfo, K, width, height)

    # generate images
    for i in range(image_count):
        # setup filename
        base_filename = "{:0{width}d}".format(i, width=format_width)
        scene.set_base_filename(base_filename)

        # set some environment texture
        filepath = expandpath(random.choice(environment_textures))
        scene.set_environment_texture(filepath)

        # actual rendering
        R = rototranslations[i]['R']  # TODO: put in right format
        t = rototranslations[i]['t']
        scene.set_pose(rotation=R, translation=t)
        scene.render()
        scene.postprocess()


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def main():
    parser = argparse.ArgumentParser(description='Render dataset for the "cap tool"', prog="blender -b -P " + __file__)
    parser.add_argument('--config', default='config/render_toolcap.cfg', help='Path to configuration file')
    parser.add_argument('--aps-path', default='~/dev/vision/amira_deep_vision', help='Path where AMIRA Perception Subsystem (aps) can be found')
    parser.add_argument('--abr-path', default='~/dev/vision/amira_blender_rendering/src', help='Path where amira_blender_rendering (abr) can be found')
    args = parser.parse_args(args=get_argv())

    # special imports. will also set system path for abr and aps
    import_aps(args.aps_path)
    import_abr(args.abr_path)

    # read configuration file
    # TODO: change to Configuration here and in foundry
    config = configparser.ConfigParser()
    config.read(expandpath(args.config))
    config = foundry.utils.check_paths(config)
    cfgs = foundry.utils.build_splitting_configs(config)

    for cfg in cfgs:
        # build directory structure and run rendering
        # TODO: rename all configs from output_dir to output_path
        dirinfo = RenderedObjects.build_directory_info(cfg['dataset']['output_dir'])

        # generate it
        generate_dataset(cfg, dirinfo)

        # save configuration
        foundry.utils.dump_config(cfg, dirinfo.base_path)
    
    # check if and create viewsphere
    if 'viewsphere' in config:
        output_dir = config['viewsphere'].get('output_dir', os.path.join(config['dataset']['output_dir'], 'Viewsphere'))
        dirinfo = RenderedObjects.build_directory_info(output_dir)
        generate_viewsphere(config, dirinfo)
        foundry.utils.dump_config(config, dirinfo.base_path)


if __name__ == "__main__":
    main()
