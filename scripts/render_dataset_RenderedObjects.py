#!/usr/bin/env python

"""This script can be used to generate RenderedObjects datasets of the cap tool.

The script must be run in blender, for instance from the command line using:

    $ blender -b -P scripts/render_dataset_RenderedObjects.py

The script accepts several additional arguments. The most important is the path
to the render configuration file, which defaults to 'config/render_toolcap.cfg'.
The script also needs to find amira_blender_rendering, as well as aps (AMIRA
Perception Subsystem) and foundry (also part of amira_perception). Path to
their parent-folders can be passed along as command-line arguments via the
--arb-path and --aps-path flags.s

Example:

    $ blender -b -P scripts/render_dataset_RenderedObjects.py -- --arb-path ~/amira/amira_blender_rendering --aps-path ~/amira/amira_perception

Note that paths will be expanded, i.e. variables such as $AMIRA_DATASETS or ~
will be turned into their proper values.

"""


# make amira_perception packages available
import bpy
import sys
import os
import argparse
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

    import foundry
    import foundry.utils

    # additional
    global ViewSampler
    from aps.data.utils.viewspheresampler import ViewSampler


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
    randomly select from a directory
    
    Args:
        cfg(Configuration): config with render setup
    """
    # this rise a KeyError if 'environment_texture' not in cfg
    environment_textures = expandpath(cfg.environment_texture)
    if os.path.isdir(environment_textures):
        files = os.listdir(environment_textures)
        environment_textures = [os.path.join(environment_textures, f) for f in files]
    else:
        environment_textures = [environment_textures]

    return environment_textures


def get_scene_type(type_str: str):
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
        'PandaTable': abr.scenes.PandaTable,
        'ClutteredPandaTable': abr.scenes.ClutteredPandaTable,
        'MultiObjectsClutteredPandaTable': abr.scenes.MultiObjectsClutteredPandaTable
    }
    if type_str not in scene_types:
        known_types = str([k for k in scene_types.keys()])[1:-1]
        raise Exception(f"Scene type {type_str} unknown. Known types: {known_types}. Note: types are case sensitive.")
    return scene_types[type_str]


def setup_renderer(cfg):
    """Setup blender CUDA rendering, and specify number of samples per pixel to
    use during rendering. If the setting render_setup.samples is not set in the
    configuration, the function defaults to 128 samples per image.
    
    Args:
        cfg(Configuration): render configuration
    """
    abr.blender_utils.activate_cuda_devices()
    n_samples = int(cfg.samples) if 'samples' in cfg else 128
    bpy.context.scene.cycles.samples = n_samples


def generate_dataset(cfg, output_path, scene=None, viewsphere_cfg=None):
    """Generate images and metadata for a dataset, specified by cfg and dirinfo

    Args:
        cfg: Configuration for the dataset
        output_path(str): path to directory for file writing
        *scene(bpy.scene): an already setup scene to render
        *viewsphere_cfg(Configuration): viewsphere configurations
    """

    # build directory structure from cfg
    dirinfo = RenderedObjects.build_directory_info(output_path)

    if viewsphere_cfg:
        rototranslations = ViewSampler.viewsphere_rototranslations(
            min_n_views=int(viewsphere_cfg['min_num_views']),
            radius=float(viewsphere_cfg['radius']) / 1000,  # convert radius from mm to m
            num_inplane_rot=int(viewsphere_cfg['viewsphere']['num_inplane_rotations']),
            convention='opengl'
        )

        # compute image count and ovewrite cfg to be dumped
        image_count = len(rototranslations)
        cfg['dataset']['image_count'] = str(image_count)
    else:
        # retrieve image count and finish, when there are no images to generate
        image_count = int(cfg['dataset']['image_count'])

    if image_count <= 0:
        return False, None

    # setup the render backend and retrieve paths to environment textures
    render_cfg = cfg.render_setup
    setup_renderer(render_cfg)
    environment_textures = get_environment_textures(render_cfg)

    # filename setup
    format_width = int(ceil(log(image_count, 10)))
    base_filename = "{:0{width}d}".format(0, width=format_width)

    # camera / output setup
    camera_info = aps.core.cv.camera.CameraInfo(
        name=cfg.camera_info.name,
        width=int(cfg.camera_info.width),
        height=int(cfg.camera_info.height),
        K=np.fromstring(cfg['camera_info']['K'], sep=',').reshape((3, 3)) if 'K' in cfg.camera_info else None
    )
    # width = int(cfg['camera_info']['width'])
    # height = int(cfg['camera_info']['height'])
    # K = None
    # if 'K' in cfg['camera_info']:
    #    K = np.fromstring(cfg['camera_info']['K'], sep=',').reshape((3, 3))

    # instantiate scene if necessary
    if scene is None:
        scene_type = get_scene_type(render_cfg.scene_type)
        # scene = scene_type(base_filename, dirinfo, K, width, height, config=cfg)
        scene = scene_type(base_filename, dirinfo, camera_info, config=render_cfg)
    else:
        scene.update_dirinfo(dirinfo)

    # generate images
    i = 0
    while i < image_count:
        # setup filename
        base_filename = "{:0{width}d}".format(i, width=format_width)
        scene.set_base_filename(base_filename)

        # set some environment texture, randomize, and render
        filepath = expandpath(random.choice(environment_textures))
        scene.set_environment_texture(filepath)

        # check whether viewsphere or dataset generation
        if viewsphere_cfg:
            scene.set_pose(pose=rototranslations[i])
        else:
            scene.randomize()
        # render
        scene.render()

        # postprocess
        try:
            scene.postprocess()
        except ValueError:
            # This issue happens every now and then. The reason might be (not
            # yet verified) that the target-object is occluded. In turn, this
            # leads to a zero size 2D bounding box...
            print(f"ValueError during post-processing, re-generating image index {i}")
            # TODO: during viewsphere generation it might happend that poses cannot
            # be rendered. Check if these cases are already addressed by try-catch
        else:
            # increment loop counter
            i = i + 1

    # See comment in renderedobjectsbase for exaplanation of reset()
    return True, scene.reset()


# def generate_viewsphere(cfg, output_path):
#     """Generate images and metadata for a view sphere, specified by cfg and dirinfo

#     Args:
#         cfg: config from configuration file
#         dirinfo(struct): structure with directory information. See RenderedObjects.build_directory_info
#     """
#     # build directory info
#     dirinfo = RenderedObjects.build_directory_info(output_path)

#     # sample views in camera frame
#     # This requires amira_perception feature/aae-computations-inspection
#     # until it is not merged to master since the methods have been made static
#     rototranslations = ViewSampler.viewsphere_rototranslations(
#         min_n_views=int(cfg['viewsphere']['min_num_views']),
#         radius=float(cfg['viewsphere']['radius']) / 1000,  # convert radius from mm to m
#         num_inplane_rot=int(cfg['viewsphere']['num_inplane_rotations']),
#         convention='opengl'
#     )

#     # compute image count and ovewrite cfg to be dumped
#     image_count = len(rototranslations)
#     cfg['dataset']['image_count'] = str(image_count)

#     # setup rendered
#     render_cfg = cfg.render_setup
#     setup_renderer(render_cfg)
#     environment_textures = get_environment_textures(render_cfg)

#     # filename setup
#     format_width = int(ceil(log(image_count, 10)))
#     base_filename = "{:0{width}d}".format(0, width=format_width)

#     # scene setup with a calibrated camera.
#     # NOTE: at the moment there is a bug in abr.camera_utils:opencv_to_blender,
#     #       which prevents us from actually using a calibrated camera. Still, we
#     #       pass it along here because at some point, we might actually have
#     #       working implementation ;)
#     width = int(cfg['camera_info']['width'])
#     height = int(cfg['camera_info']['height'])
#     K = None
#     if 'K' in cfg['camera_info']:
#         K = np.fromstring(cfg['camera_info']['K'], sep=',')

#     # instantiate scene
#     scene_type = get_scene_type(cfg['render_setup']['scene_type'])
#     scene = scene_type(base_filename, dirinfo, K, width, height)

#     # generate images
#     for i in range(image_count):
#         # setup filename
#         base_filename = "{:0{width}d}".format(i, width=format_width)
#         scene.set_base_filename(base_filename)

#         # set some environment texture
#         filepath = expandpath(random.choice(environment_textures))
#         scene.set_environment_texture(filepath)

#         # set pose (expressed in camera frame. it is tranformerd into world frame: see set_pose) and render
#         scene.set_pose(pose=rototranslations[i])
#         scene.render()
#         scene.postprocess()

#     # reset in case this is required. Otherwise might lead to blender segfault
#     scene.reset()


def get_argv():
    """Get argv after --"""
    try:
        # only arguments after --
        return sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        return []


def get_cmd_argparser():
    parser = argparse.ArgumentParser(
        description='Render dataset in blender', prog="blender -b -P " + __file__,
        add_help=False)
    parser.add_argument('--config', default='config/render_toolcap.cfg', help='Path to configuration file')
    parser.add_argument('--aps-path', default='~/dev/vision/amira_perception',
                        help='Path where AMIRA Perception Subsystem (aps) can be found')
    parser.add_argument('--abr-path', default='~/dev/vision/amira_blender_rendering/src',
                        help='Path where amira_blender_rendering (abr) can be found')
    parser.add_argument('--only-viewsphere', action='store_true', help='Generate only Viewsphere dataset')
    parser.add_argument('--print-config', action="store_true", help='Print configuration and exit')
    parser.add_argument('-h', '--help', action='store_true', help='Print this help message and exit')
    
    return parser


def get_basic_config():
    "Setup script specific configuration"
    
    # basic config parameters
    config = aps.core.utils.datastructures.Configuration()

    config.add_param('dataset.image_count', 0, 'Number of images to generate')
    config.add_param('dataset.output_path', '', 'Path to storage directory')

    config.add_param('camera_info.name', 'none', 'Name for camera')
    config.add_param('camera_info.width', 640, 'Rendered image resolution (pixel) along x (width)')
    config.add_param('camera_info.height', 480, 'Rendered image resolution (pixel) along y (height)')

    config.add_param('render_setup.backend', 'blender-cycles', 'Render backend. Blender only one supported')
    config.add_param('render_setup.scene_type', '', 'Scene type to be rendered')
    config.add_param('render_setup.target_objects', '', '(List of) target objects in the scene', special='maybe_list')
    config.add_param('render_setup.blend_file', '', 'Path to .blend file with modeled scene')

    return config


def main():
    # parse command arguments
    cmd_parser = get_cmd_argparser()
    cmd_args = cmd_parser.parse_args(args=get_argv())  # need to parse to get aps and abr

    # special imports. will also set system path for abr and aps
    import_aps(cmd_args.aps_path)
    import_abr(cmd_args.abr_path)

    # setup and parse configuration
    config = get_basic_config()

    # combine parsers and parse
    parser = argparse.ArgumentParser(
        prog="blender -b -P " + __file__,
        parents=[cmd_parser] + config.get_argparsers(),
        add_help=False)
    args = parser.parse_args(args=get_argv())

    # check if there's a config file
    if ('config' in args) and (args.config is None):
        print("Please specify a configuration file with the '--config' argument.")
        parser.print_help()
        sys.exit()

    configfile = expandpath(args.config)
    if not os.path.exists(configfile):
        raise RuntimeError(f"Configuration file '{configfile}' does not exist")

    # parse file and command line
    config.parse_file(configfile)
    config.parse_args()
    config = foundry.utils.check_paths(config)  # check and expand principal paths

    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.print_config:
        print(config.to_cfg())
        sys.exit(0)

    # split configuration
    cfgs = foundry.utils.build_splitting_configs(config)

    # skip if only viewsphere dataset is selected
    scene = None
    if not args.only_viewsphere:
        for cfg in cfgs:
            # generate it, reusing a potentially established scene
            output_path = cfg.dataset.output_path
            success, scene = generate_dataset(cfg, output_path, scene=scene)
            if success:
                # save configuration
                foundry.utils.dump_config(cfg, output_path)
            else:
                print(f"EE: Error while generating dataset")
                scene = None

    # check if and create viewsphere
    if 'viewsphere' in config:
        output_path = expandpath(
            config['viewsphere'].get('output_path', os.path.join(config['dataset']['output_path'], 'Viewsphere')))
        generate_dataset(config, output_path, viewsphere_cfg=config['viewsphere'])
        foundry.utils.dump_config(config, output_path)


if __name__ == "__main__":
    main()
