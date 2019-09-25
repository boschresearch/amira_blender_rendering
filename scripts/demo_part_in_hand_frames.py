# FIXME: workout using Blender (bpy) as a python module
"""For running within Blender python console copy-paste the lines below:

import os.path as osp
import sys
pkg_dir = "/home/yoelsh/work/amira_blender_rendering" #TODO: customize to your PC
sys.path.append(osp.join(pkg_dir, "src"))
sys.path.append(osp.join(pkg_dir, "scripts"))
import demo_part_in_hand_frames
panda = demo_part_in_hand_frames.run()
"""
import os.path as osp
import time
import numpy as np

import bpy
from mathutils import Vector, Matrix

from amira_blender_rendering import robot_driver, utils
from amira_blender_rendering import blender_utils as blnd

scripts_dir = utils.get_my_dir(__file__)
pkg_dir = osp.split(scripts_dir)[0]
out_dir = osp.join(pkg_dir, "out")
output_file = osp.join(out_dir, "image_{:04}")

version_ge_2_8 = bpy.app.version[1] >= 80


def scene_setup():

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.frame_start = 1
    scene.frame_current = 1
    scene.frame_end = 10

    render = scene.render
    render.filepath = osp.join(out_dir, "panda_demo_")
    render.image_settings.file_format = "JPEG"
    render.resolution_x = 640
    render.resolution_y = 480

    try:
        scene.cycles.device = 'GPU'
        render.resolution_x = 1280
        render.resolution_y = 960
    except TypeError:
        pass

    if version_ge_2_8:
        pass  # TODO : configure params to avoid fireflies, etc.
    else:
        try:
            for layer in render.layers:
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

    return scene, render


def run():

    # timestamp = time.strftime("%Y%b%d-%H%M%S")

    scene, render = scene_setup()

    blnd.clear_all_objects()
    blnd.create_room_corner()

    # lighting
    if version_ge_2_8:
        bpy.ops.object.light_add(type='SUN', location=(1, 2, 2))
        sun_name = bpy.data.lights[-1].name
    else:
        bpy.ops.object.lamp_add(type='SUN', radius=1, view_align=False, location=(1, 2, 2))
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

    # robot
    panda = robot_driver.PandaIKDriver()

    # eBike parts
    gear = blnd.load_cad_part("Gear-Wheel")
    blnd.translate_object(gear, (0.45, -0.2, 0.0))

    shaft = blnd.load_cad_part("Shaft")
    shaft_bbox = blnd.get_mesh_bounding_box(shaft)

    panda.gripper.set_to(shaft_bbox.x.max)

    # images
    if version_ge_2_8:
        dg = bpy.context.evaluated_depsgraph_get()

    for k_img in range(1, 9):

        if k_img > 1:
            panda.randomize_tcp(xlim=(0.1, 10), ylim=(-0.2, 10))

        if version_ge_2_8:
            dg.update()
        else:
            scene.update()  # must update panda.tcp.matrix_world

        shaft.matrix_world = panda.tcp.matrix_world
        if k_img > 3:

            panda.gripper.set_to(shaft_bbox.y.max)

            # rotating part inside gripper
            H = np.array(shaft.matrix_world)
            R_new = np.dot(H[:3, :3], Matrix.Rotation(np.deg2rad(90), 3, (0, 1, 0)))
            H[:3, :3] = R_new
            shaft.matrix_world = Matrix(H)
            # if this breaks, try fall-back to the command below:
            # bpy.ops.transform.rotate(
            #   value=np.deg2rad(90), constraint_axis=(False, True, False), constraint_orientation='LOCAL')
            # BUT make sure to deselect all, and select\active the shaft object

        render.filepath = output_file.format(k_img)
        bpy.ops.render.render(write_still=True)

    # nice for debug
    return panda


if __name__ == "__main__":
    run()
