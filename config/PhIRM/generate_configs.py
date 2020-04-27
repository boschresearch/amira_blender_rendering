#!/usr/bin/env python3

# Yes, we are lazy. Why should we create all the configuration files manually,
# if we have computers that can do the job?

#
# Setup what should be generated and how
#

# Train and test split
modes  = ['Train', 'Test']

# image count per train / test
images = [1, 1]

# directory prefix
dirprefix = "Workstation"

# scenario selection from the workstations environment
scenarios = [0, 1, 3]

# Target object specification. We will simply enumerate the objects, so that we
# do not need to refer to them by name in the configurations below
target_objects = [
        # RefID, Identifier in 'target_objects'
        # PhIRM
        [0,  'parts.bundmutter_m8'],
        [1,  'parts.hammerschraube'],
        [2,  'parts.karabinerhaken'],
        [3,  'parts.sterngriff'],
        [4,  'parts.strebenprofil_20x20'],
        [5,  'parts.winkel_60x60'],
        [6,  'parts.wuerfelverbinder_40x40'],
        # T-Less. Randomly selected from all T-Less objects
        [7,  'parts.tless_obj_06'],
        [8,  'parts.tless_obj_13'],
        [9,  'parts.tless_obj_20'],
        [10, 'parts.tless_obj_27'],
]

# object configurations, i.e. which objects to pair in which configuration. If
# there should be no combination, simply add a single-item list entry.
# Configurations C and D were chosen by a fair dice roll (https://xkcd.com/221/).
obj_sets = {
        'A': [[i] for i in range(7)],
        'B': [[i] for i in range(7)],
        'C': [[2,3],[5,6]],
        'D': [[0,2,5],[1,3,6]],
        'E': [[0,1,2,3,4,5,6]],
        'F': [list(range(7, 11))]
}

# number of instances per object in the different configurations
obj_instances = {
        'A': 1,
        'B': 5,
        'C': 2,
        'D': 3,
        'E': 2,
        'F': 3,
}

# specify for which configuration we want to produce multi-view output
gen_multi_view = {
        'A': True,
        'B': True,
        'C': False,
        'D': False,
        'E': False,
        'F': True,
}

# specify how many frames we want to forward simulate each Configuration
forward_frames = {
        'A': 10,
        'B': 10,
        'C': 10,
        'D': 10,
        'E': 10,
        'F': 10,
}

# select which configurations to generate
target_configs = ['A', 'B', 'C', 'D', 'E', 'F']


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
def get_scene_setup(fframes, multi_view=False):
    cameras = "Camera" if not multi_view else "Camera, StereoCamera.Left, StereoCamera.Right"
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

def gen_config(C, obj_sets, ninstances, fframes, multi_view=True):
    # setup all configurations
    for s in scenarios:
        for oset in obj_sets:
            # construct object identifier string for base name
            o = '_'.join([str(obj_id) for obj_id in oset])

            # construct target objects
            targets = [target_objects[obj_id][1] for obj_id in oset]
            targets = [t + f':{ninstances}' for t in targets]
            targets = ", ".join(targets)

            for m, mode in enumerate(modes):
                base_name = f"{dirprefix}-{mode}-C{C}-S{s}-O{o}"
                base_path = f"$AMIRA_DATASETS/PhIRM/{base_name}"

                cfg = get_dataset(images[m], base_path) + '\n' \
                    + camera_info + '\n' \
                    + render_setup + '\n' \
                    + get_scene_setup(fframes, multi_view) + '\n' \
                    + parts + '\n' \
                    + get_scenario_setup(s, targets)

                fname = f"{base_name}.cfg"
                with open(fname, 'w') as f:
                    f.write(cfg)

if __name__ == "__main__":
    for C in target_configs:
        print(f"Generating configs for Configuration {C}")
        gen_config(C, obj_sets[C], obj_instances[C], forward_frames[C], gen_multi_view[C])
