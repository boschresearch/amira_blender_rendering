# FIXME: workout using Blender (bpy) as a python module
"""For running within Blender python console copy-paste the lines below:

import os.path as osp
import sys
pkg_dir = "/home/yoelsh/work/amira_tools/amira_blender_rendering" #TODO: customize to your PC
sys.path.append(osp.join(pkg_dir, "src"))
sys.path.append(osp.join(pkg_dir, "scripts"))
import cad_parts_video_demo
cad_parts_video_demo.run()
"""
import os.path as osp
import time
import numpy as np

import bpy
from mathutils import Vector

from amira_blender_rendering import robot_driver, utils
from amira_blender_rendering import blender_utils as blnd

scripts_dir = utils.get_my_dir(__file__)
pkg_dir = osp.split(scripts_dir)[0]
out_dir = osp.join(pkg_dir, "out")
utils.try_makedirs(out_dir)
src_dir = osp.join(pkg_dir, "src", "amira_blender_rendering")
assets_dir = osp.join(src_dir, "assets")


def run():

    # timestamp = time.strftime("%Y%b%d-%H%M%S")

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.frame_start = 1
    scene.frame_end = 45
    scene.frame_current = 1

    render = scene.render
    render.filepath = osp.join(out_dir, "panda_demo_")
    render.image_settings.file_format = "FFMPEG"
    render.resolution_x = 640
    render.resolution_y = 480

    try:
        scene.cycles.device = 'GPU'
        render.resolution_x = 1280
        render.resolution_y = 960
    except TypeError:
        pass

    # Assuming single layer
    try:
        layer = render.layers[0]
        layer.cycles.use_denoising = True
        layer.cycles.denoising_radius = 5
        layer.cycles.denoising_strength = 0.3
        layer.cycles.denoising_feature_strength = 0.3
        layer.cycles.denoising_diffuse_direct = False
        layer.cycles.denoising_transmission_direct = False
        layer.cycles.denoising_subsurface_direct = False
    except Exception as err:
        print("failed to set denoising")
        print(err)

    blnd.clear_all_objects()
    blnd.create_room_corner()

    # lighting
    bpy.ops.object.lamp_add(
        type='SUN',
        radius=1,
        view_align=False,
        location=(1, 2, 2),
    )
    sun_name = bpy.data.lamps[-1].name
    sun = bpy.data.objects[sun_name]
    sun.name = "Sun"
    sun.rotation_mode = 'XYZ'
    sun.rotation_euler.x = -0.2

    # camera
    bpy.ops.object.camera_add(
        enter_editmode=False,
        location=(1.2, 1.2, 1.4),
        rotation=(np.deg2rad(60), 0, np.deg2rad(135)),
    )
    cam_name = bpy.data.cameras[0].name
    cam = bpy.data.objects[cam_name]
    cam.name = "Camera_1"
    cam.scale = Vector((0.15, 0.15, 0.15))

    scene.camera = cam

    # eBike parts
    shaft = blnd.load_cad_part("Shaft")
    blnd.translate_object(shaft, (0.4, -0.1, 0.0))

    gear = blnd.load_cad_part("Gear-Wheel")
    blnd.translate_object(gear, (0.45, -0.2, 0.0))

    # robot
    panda = robot_driver.PandaIKDriver()
    panda.base.rotate(90, (0, 0, 1))
    panda.tcp.set_position((-0.15, 0.45, 0.4))

    # keyframes
    panda.tcp.keyframe_insert(data_path='location', frame=(1))

    panda.tcp.set_position((0.4, -0.1, 0.3))
    panda.tcp.keyframe_insert(data_path='location', frame=(10))

    panda.gripper.set_to(1)
    panda.gripper.keyframe_insert(data_path='location', frame=(15))

    panda.tcp.set_position((0.4, -0.1, 0.0))
    panda.tcp.keyframe_insert(data_path='location', frame=(25))

    panda.gripper.set_to(0.0125)
    panda.gripper.keyframe_insert(data_path='location', frame=(30))

    panda.tcp.set_position((0.4, -0.1, 0.4))
    panda.tcp.keyframe_insert(data_path='location', frame=(40))

    # save blend file
    out_file = osp.join(out_dir, "Panda_demo.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_file)

    # render to video
    print("Finished making scene, starting to render animation")
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    run()
