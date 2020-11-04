#!/usr/bin/env python3

# Yes, we are lazy. Why should we create all the configuration files manually,
# if we have computers that can do the job?

#
# Setup what should be generated and how
#

# dataset type
modes = ['Detection', 'Tracking']

# scene/view count per mode per camera
images = {
    modes[0]: [100, 5],
    modes[1]: [1, 100]
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
    'A': [0, 1],
    'B': [2, 3],
    'C': [4, 5, 6],
    'D': [0, 2, 4, 6],
    'E': [0, 1, 2, 3, 4, 5, 6, 7, 8],
    'F': [0, 7],
    'G': [1, 8],
    'H': [1, 2, 3],
    'I': [1, 3, 5, 7],
    'L': [1, 2, 3, 4, 5, 6, 7, 8],
}

target_scenes = {
    'A': 'robottable_empty_no_cameraframe',
    'B': 'robottable_empty_no_cameraframe',
    'C': 'robottable_empty_no_cameraframe',
    'D': 'robottable_empty_no_cameraframe',
    'E': 'robottable_empty_no_cameraframe',
    'F': 'robottable_distractors_no_cameraframe',
    'G': 'robottable_distractors_no_cameraframe',
    'H': 'robottable_distractors_no_cameraframe',
    'I': 'robottable_distractors_no_cameraframe',
    'L': 'robottable_distractors_no_cameraframe',
}

# specify for which mode we want to produce multi-view output
multi_view = {
    modes[0]: {
        'enabled': True,
        'A': 'linear',
        'B': 'linear',
        'C': 'linear',
        'D': 'linear',
        'E': 'linear',
        'F': 'linear',
        'G': 'linear',
        'H': 'linear',
        'I': 'linear',
        'L': 'linear',
    },
    modes[1]: {
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
        'L': 'circle',
    }
}

# specify for which mode we want to produce motion blur
motion_blur = {
    modes[0]: False,
    modes[1]: True
}

# specify how many frames we want to forward simulate each Configuration
forward_frames = 50

# specify object(s) in the scene whose textures are randommized
textured_objs_sets = {
    'A': {'objects': [], 'textures': ''},
    'B': {'objects': [], 'textures': ''},
    'C': {'objects': [], 'textures': ''},
    'D': {'objects': [], 'textures': ''},
    'E': {'objects': [], 'textures': ''},
    'F': {'objects': ['RubberPlate'], 'textures': '$DATA/models/object_textures'},
    'G': {'objects': ['RubberPlate'], 'textures': '$DATA/models/object_textures'},
    'H': {'objects': ['RubberPlate'], 'textures': '$DATA/models/object_textures'},
    'I': {'objects': ['RubberPlate'], 'textures': '$DATA/models/object_textures'},
    'L': {'objects': ['RubberPlate'], 'textures': '$DATA/models/object_textures'},
}

# select which configurations to generate
target_configs = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L']

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
camera_info = """[camera_info]
width = 960
height = 540
model = pinhole
name = RealSenseD435
zeroing = 0, 0, 0
intrinsic = 698.128, 698.617, 478.459, 274.426
intrinsics_conversion_mode = mm
"""


# [render_setup]
def get_render_setup(motion_blur: bool = True):
    return f"""[render_setup]
backend = blender-cycles
integrator = BRANCHED_PATH
denoising = True
samples = 32
allow_occlusions = True
motion_blur = {motion_blur}
"""


# [scene_setup]
def get_scene_setup(fframes: int = 20, blend_file: str = 'robottable_empty'):
    return f"""[scene_setup]
blend_file = $DATA_STORAGE/models/scenes/{blend_file}.blend
environment_textures = $DATA_STORAGE/OpenImagesV4/Images
cameras = Camera.FrontoParallel.Left, Camera.FrontoParallel.Right
forward_frames = {fframes}
"""


# [postprocess]
postprocess = """[postprocess]
depth_scale = 1000.0
compute_disparity = True
parallel_cameras = Camera.FrontoParallel.Left, Camera.FrontoParallel.Right
parallel_cameras_baseline_mm = 50
"""


# TODO
# [multiview_setup]
def get_multiview_setup(mode: str = 'wave'):
    if mode == 'wave':
        cfg_str = """mode_config.center = -0.75, 0., 1.8
mode_config.radius = 0.5
mode_config.frequency = 4
mode_config.amplitude = 0.28
"""
    elif mode == 'circle':
        cfg_str = """mode_config.center = -0.75, 0., 1.5
mode_config.radius = 0.45
"""
    elif mode == 'linear':
        cfg_str = """mode_config.p0 = 0, 0, 0
mode_config.p1 = 0.1, 0, -0.5
mode_config.offset =
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


def gen_config(C, trgt_objs_set, txt_objs_set):

    # construct target objects
    targets = [f'{target_objects[obj_id][0]}:{target_objects[obj_id][1]}' for obj_id in trgt_objs_set]
    targets = ", ".join(targets)

    # construct textured objects
    textured_objects = ", ".join(txt_objs_set['objects'])
    object_textures = txt_objs_set['textures']

    for mode in modes:
        base_path = f"$AMIRA_DATASETS/{dataset_name}/{mode}/Configuration{C}"

        if multi_view[mode]['enabled']:
            multi_view_mode = multi_view[mode][C]
            dset_str = get_dataset(images[mode][0] * images[mode][1], base_path,
                                   nscenes=images[mode][0], nviews=images[mode][1])
            multi_view_str = get_multiview_setup(multi_view_mode)
        else:
            dset_str = get_dataset(images[mode], base_path, nscenes=images[mode])
            multi_view_str = ''

        cfg = dset_str + '\n' \
            + camera_info + '\n' \
            + get_render_setup(motion_blur[mode]) + '\n' \
            + get_scene_setup(forward_frames, target_scenes[C]) + '\n' \
            + multi_view_str + '\n' \
            + postprocess + '\n' \
            + parts + '\n' \
            + get_scenario_setup(targets, textured_objects, object_textures)

        fname = f"cfgs/tmp-{mode}-C{C}.cfg"
        with open(fname, 'w') as f:
            f.write(cfg)


if __name__ == "__main__":
    for C in target_configs:
        print(f"Generating configs for Configuration {C}")
        gen_config(C, target_obj_sets[C], textured_objs_sets[C])
