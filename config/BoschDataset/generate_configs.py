#!/usr/bin/env python3

# Yes, we are lazy. Why should we create all the configuration files manually,
# if we have computers that can do the job?

#
# Setup what should be generated and how
#

# dataset type
modes = ['Detection', 'Tracking']

# select which configurations to generate
target_configs = {
    'Detection': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
    'Tracking': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
}

# select resolution (currently high, medium, low). See specs below
# NOTE: this affects the output base_path as well.
resolution = 'low'

# define camera data based on resolution level [width, height, intrinsics]
camera_data = {
    'low': '390.30499267578125, 390.30499267578125, 320, 240',
    'medium': '698.128, 698.617, 478.459, 274.426',
    'high': '650.50830078125, 650.50830078125, 640, 360',
}


# scene types to load
scene_types = {
    'Detection': 'PandaTable',
    'Tracking': 'StaticScene'
}

# scene/view count per mode per camera per config
images = {
    'Detection': {
        'A': [1000, 4],
        'B': [500, 4],
        'C': [500, 4],
        'D': [500, 4],
        'E': [500, 4],
        'F': [500, 4],
        'G': [500, 4],
        'H': [1000, 4],
    },
    'Tracking': {
        'A': [1, 1000],
        'B': [1, 1000],
        'C': [1, 1000],
        'D': [1, 1000],
        'E': [1, 1000],
        'F': [1, 1000],
        'G': [1, 1000],
        'H': [1, 1000],
        'I': [1, 1000],
        'J': [1, 1000],
        'K': [1, 1000],
        'L': [1, 1000],
    }
}

# Target object specification. We will simply enumerate the objects, so that we
# do not need to refer to them by name in the configurations below
target_objects = {
    # RefID, Identifier in 'target_objects', number of instances
    # target objects
    0: ['parts.ObjectCarrier', 1],
    1: ['parts.ToolCap', 2],
    2: ['parts.GearWheel', 2],
    3: ['parts.DriveShaft', 2],
    4: ['parts.sterngriff', 2],
    5: ['parts.winkel_60x60', 2],
    6: ['parts.wuerfelverbinder_40x40', 2],
    7: ['parts.tless_obj_04', 2],
    8: ['parts.tless_obj_10', 2]
}

# object configurations, i.e. which objects to pair in which configuration.
target_obj_sets = {
    'Detection': {
        'A': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'B': [0, 8],
        'C': [1, 7],
        'D': [0, 1, 2, 3],
        'E': [4, 5, 6, 7],
        'F': [0, 2, 3, 5, 6, 7],
        'G': [1, 3, 4, 5, 6, 8],
        'H': [0, 1, 2, 3, 4, 5, 6, 7, 8],
    },
    'Tracking': {
        'A': [0, 1, 2, 5, 6],
        'B': [0, 1, 2, 5, 6],
        'C': [0, 1, 2, 5, 6],
        'D': [0, 1, 2, 5, 6],
        'E': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'F': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'G': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'H': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'I': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'J': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'K': [0, 1, 2, 3, 4, 5, 6, 7, 8],
        'L': [0, 1, 2, 3, 4, 5, 6, 7, 8],
    }
}

target_scenes = {
    'Detection': {
        'A': 'robottable_empty_no_cameraframe',
        'B': 'robottable_distractors_no_cameraframe',
        'C': 'robottable_distractors_no_cameraframe',
        'D': 'robottable_distractors_no_cameraframe',
        'E': 'robottable_distractors_no_cameraframe',
        'F': 'robottable_distractors_no_cameraframe',
        'G': 'robottable_distractors_no_cameraframe',
        'H': 'robottable_distractors_no_cameraframe',
    },
    'Tracking': {
        'A': 'robottable_static_some_objects_no_cameraframe',
        'B': 'robottable_static_some_objects_no_cameraframe',
        'C': 'robottable_static_some_objects_no_cameraframe',
        'D': 'robottable_static_some_objects_no_cameraframe',
        'E': 'robottable_static_all_objects_no_cameraframe',
        'F': 'robottable_static_all_objects_no_cameraframe',
        'G': 'robottable_static_all_objects_no_cameraframe',
        'H': 'robottable_static_all_objects_no_cameraframe',
        'I': 'robottable_static_all_objects_distractors_no_cameraframe',
        'J': 'robottable_static_all_objects_distractors_no_cameraframe',
        'K': 'robottable_static_all_objects_distractors_no_cameraframe',
        'L': 'robottable_static_all_objects_distractors_no_cameraframe',
    }
}

# specify for which mode we want to produce multi-view output
multi_view = {
    'Detection': {
        'enabled': True,
        'A': 'random',
        'B': 'random',
        'C': 'random',
        'D': 'random',
        'E': 'random',
        'F': 'random',
        'G': 'random',
        'H': 'random',
    },
    'Tracking': {
        'enabled': True,
        'A': 'wave',
        'B': 'circle',
        'C': 'wave',
        'D': 'circle',
        'E': 'wave',
        'F': 'circle',
        'G': 'wave',
        'H': 'circle',
        'I': 'wave',
        'J': 'circle',
        'K': 'wave',
        'L': 'circle',
    }
}

# specify how many frames we want to forward simulate each Configuration
forward_frames = {
    'Detection': 50,
    'Tracking': ''
}

render_data = {
    'low': [640, 480],
    'medium': [960, 540],
    'high': [1280, 720],
    'num_samples': 64,
    'motion_blur': {
        'Detection': False,
        'Tracking': True
    }
}

# specify object(s) in the scene whose textures are randommized
textured_objs_sets = {
    'Detection': {
        'A': {'objects': [], 'textures': ''},
        'B': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'C': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'D': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'E': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'F': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'G': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
        'H': {'objects': ['RubberPlate', 'TableTop'], 'textures': '$DATA_STORAGE/assets/textures/detection'},
    },
    'Tracking': {
        'A': {'objects': [], 'textures': ''},
        'B': {'objects': [], 'textures': ''},
        'C': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
        'D': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
        'E': {'objects': [], 'textures': ''},
        'F': {'objects': [], 'textures': ''},
        'G': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
        'H': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
        'I': {'objects': [], 'textures': ''},
        'J': {'objects': [], 'textures': ''},
        'K': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
        'L': {'objects': ['RubberPlate'], 'textures': '$DATA_STORAGE/assets/textures/tracking/Wood023_2K_Color.png'},
    },
}


# name of dataset, used as target directory
dataset_name = 'BoschDataset'


# Configuration file parts
#
# [dataset]
def get_dataset(nimages, base_path, nscenes: int = 1, nviews: int = 1, scene_type: str = 'PandaTable'):
    return f"""[dataset]
image_count = {nimages}
scene_count = {nscenes}
view_count = {nviews}
base_path = {base_path}
scene_type = {scene_type}
"""


# [camera_info]
camera_group_info = f"""[camera_fronto_parallel]
zeroing = 0, 0, 0
intrinsic = {camera_data[resolution]}
intrinsics_conversion_mode = mm
center = ParallelCameraCenter
aim =  ParallelCameraAim
type = parallel_stereo
names = Camera.FrontoParallel.Left, Camera.FrontoParallel.Right
displacements_mm = -25, 25
compute_disparity = True
baseline_mm = 50
"""


# [render_setup]
def get_render_setup(width: int = 640, height: int = 480, num_samples: int = 32, motion_blur: bool = False):
    return f"""[render_setup]
width = {width}
height = {height}
backend = blender-cycles
integrator = BRANCHED_PATH
denoising = True
samples = {num_samples}
allow_occlusions = True
motion_blur = {motion_blur}
"""


# [scene_setup]
def get_scene_setup(fframes: int = 20, blend_file: str = 'robottable_empty', mode=''):

    open_image_path = '$DATA_STORAGE/OpenImagesV4/Images'
    hdr_texture_path = '$DATA_STORAGE/assets/textures/background/machine_shop_02_4k.hdr'

    return f"""[scene_setup]
blend_file = $DATA_STORAGE/assets/scenes/{blend_file}.blend
environment_textures = {hdr_texture_path if mode == 'Tracking' else open_image_path}
camera_groups = camera_fronto_parallel
forward_frames = {fframes}
"""


# [postprocess]
postprocess = {
    'Detection': """[postprocess]
depth_scale = 10000.0
""",
    'Tracking': """[postprocess]
depth_scale = 10000.0
# fall back to visibility computations from mask if there is any issue
visibility_from_mask = True
""",
}


# [multiview_setup]
def get_multiview_setup(mode: str = 'wave'):
    if mode == 'wave':
        cfg_str = f"""{mode}.center = 0.43, -0.005, 0.06
{mode}.radius = 0.5
{mode}.frequency = 4
{mode}.amplitude = 0.28
"""
    elif mode == 'circle':
        cfg_str = f"""{mode}.center = 0.43, -0.005, -0.23
{mode}.radius = 0.45
"""
    elif mode == 'piecewiselinear':
        cfg_str = f"""{mode}.control_points = 0, 0, 0, 0.05, -0.1, -0.1, 0.1, 0.1, -0.2
{mode}.dimension = 3
"""
    elif mode == 'random':
        cfg_str = f"""{mode}.offset = 0, 0, 0
{mode}.scale = 0.3
"""
    else:
        ValueError(f'Unknown multiview mode {mode}')

    return f"""[multiview_setup]
mode = {mode}
{cfg_str}
"""


# [parts]
with open('all_parts.cfg', 'r') as f:
    parts = f.read()


# [scenario_setup]
def get_scenario_setup(parts: str, txt_objs: str, textures: str):
    """
    Args:
        parts(str): string with list of target objects to render
        txt_objs(str): strin with list of object whose texture is randomized at render
        textures(str): path to textures
    """
    return f"""[scenario_setup]
target_objects = {parts}
textured_objects = {txt_objs}
objects_textures = {textures}
"""


def gen_config(C, trgt_objs_set, txt_objs_set, mode):

    # construct target objects
    targets = [f'{target_objects[obj_id][0]}:{target_objects[obj_id][1]}' for obj_id in trgt_objs_set]
    targets = ", ".join(targets)

    # construct textured objects
    textured_objects = ", ".join(txt_objs_set['objects'])
    object_textures = txt_objs_set['textures']

    base_path = f"$OUTDIR/{dataset_name}/{resolution}_res/{mode}/Configuration{C}"

    if multi_view[mode]['enabled']:
        multi_view_mode = multi_view[mode][C]
        dset_str = get_dataset(images[mode][C][0] * images[mode][C][1], base_path,
                               nscenes=images[mode][C][0], nviews=images[mode][C][1], scene_type=scene_types[mode])
        multi_view_str = get_multiview_setup(multi_view_mode)
    else:
        dset_str = get_dataset(images[mode], base_path, nscenes=images[mode])
        multi_view_str = ''

    cfg = dset_str + '\n' \
        + get_render_setup(render_data[resolution][0],
                           render_data[resolution][1],
                           render_data['num_samples'],
                           render_data['motion_blur'][mode]) + '\n' \
        + get_scene_setup(forward_frames[mode], target_scenes[mode][C], mode=mode) + '\n' \
        + camera_group_info + '\n' \
        + multi_view_str + '\n' \
        + postprocess[mode] + '\n' \
        + parts + '\n' \
        + get_scenario_setup(targets, textured_objects, object_textures)

    fname = f"cfgs/tmp-{resolution}_res-{mode}-C{C}.cfg"
    with open(fname, 'w') as f:
        f.write(cfg)


if __name__ == "__main__":

    for mode in modes:
        for C in target_configs[mode]:
            print(f"Generating configs for mode {mode}, Configuration {C}")
            gen_config(C, target_obj_sets[mode][C], textured_objs_sets[mode][C], mode)
