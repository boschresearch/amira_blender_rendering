#!/usr/bin/env python3

# Yes, we are lazy. Why should we create all the configuration files manually,
# if we have computers that can do the job?


# Train and test split
modes  = ['Train', 'Test']
# image count per train / test
images = [10, 1]
# directory prefix
dirprefix = "Workstation"
# scenario selection from the workstations environment
scenarios = [0, 1, 3, 4]

target_objects = [
    'parts.bundmutter_m8',
    'parts.hammerschraube',
    'parts.karabinerhaken',
    'parts.sterngriff',
    'parts.strebenprofil_20x20',
    'parts.winkel_60x60',
    'parts.wuerfelverbinder_40x40']


# Configuration file parts
#
# [dataset]
def get_dataset(nimages, base_path):
    return f"""[dataset]
image_count = {nimages}
base_path = {base_path}
scene_type = WorkstationScenarios
"""

# [camera_info]
camera_info="""[camera_info]
width = 640
height = 480
model = pinhole
name = Orbbec Astra Pro
zeroing = 0, 0, 0
intrinsic = 9.9801747708520452e+02,9.9264009290521165e+02,6.6049856967197002e+02,3.6404286361152555e+02,0
"""

# [scene_setup]
def get_scene_setup(fframes, with_stereo=False):
    cameras = "Camera" if not with_stereo else "Camera, StereoCamera.Left, StereoCamera.Right"
    return f"""[scene_setup]
blend_file = $AMIRA_DATA_GFX/modeling/workstation_scenarios.blend
environment_texture = $AMIRA_DATASETS/OpenImagesV4/Images
cameras = {cameras}
forward_frames = {fframes}
"""

# [render_setup]
render_setup="""[render_setup]
backend = blender-cycles
integrator = BRANCHED_PATH
denoising = True
samples = 64
"""

# [parts]
with open('all_parts.cfg', 'r') as f:
    parts = f.read()

# [scenario_setup]
def get_scenario_setup(scenario, parts):
    return f"""[scenario_setup]
scenario = {scenario}
target_objects = {parts}
"""


def config_AB(C, nparts, fframes):
    for s in scenarios:
        for o, obj in enumerate(target_objects):
            for m, mode in enumerate(modes):

                base_name = f"{dirprefix}-{mode}-C{C}-S{s}-O{o}"
                base_path = f"$AMIRA_DATASETS/PhIRM/{base_name}"

                cfg = get_dataset(images[m], base_path) + '\n' \
                    + camera_info + '\n' \
                    + render_setup + '\n' \
                    + get_scene_setup(fframes) + '\n' \
                    + parts + '\n' \
                    + get_scenario_setup(s, f"{obj}:{nparts}")

                fname = f"{base_name}.cfg"
                with open(fname, 'w') as f:
                    f.write(cfg)


# generate configurations
config_AB('A', 1, 10)
config_AB('B', 5, 10)


