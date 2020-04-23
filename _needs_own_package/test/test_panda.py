# TODO : test CAD imports, perhapse separate file
# FIXME: workout using Blender (bpy) as a python module
"""For running within Blender python console copy-paste the lines below:

import os.path as osp
import sys
pkg_dir = "/home/yoelsh/work/amira_blender_rendering" #TODO: customize to your PC
sys.path.append(osp.join(pkg_dir, "src"))
sys.path.append(osp.join(pkg_dir, "test"))
import test_panda
test_panda.run_tests()
"""
import unittest
import traceback as tb
import os
import os.path as osp
import time
import sys
import inspect

import bpy
from mathutils import Vector, Matrix, Quaternion

from amira_blender_rendering import utils, composite_node_material, robot_driver
from amira_blender_rendering import blender_utils as blnd

version_ge_2_8 = bpy.app.version[1] >= 80

DEG2RAD = 0.01745
X_AXIS = (1, 0, 0)
Y_AXIS = (0, 1, 0)
Z_AXIS = (0, 0, 1)

test_dir = utils.get_my_dir(__file__)
parent, _ = osp.split(test_dir)
out_dir = osp.join(parent, "out")
temp_dir = osp.join(out_dir, "temp")
test_out_dir = osp.join(out_dir, "test")
assets_dir = osp.join(parent, "src/amira_blender_rendering/assets")

utils.try_makedirs(out_dir)
utils.try_rmtree(test_out_dir)
utils.try_makedirs(test_out_dir)


def _flatten_test_results_file(test_name, timeout=20, sleep=1):
    t0 = time.time()
    while (time.time() - t0) < timeout:
        for suffix in [".png", ".jpg"]:
            img = osp.join(temp_dir, "image{}".format(suffix))
            if osp.isfile(img):
                dst = osp.join(test_out_dir, test_name + suffix)
                utils.try_move(img, dst)
                return
        time.sleep(sleep)


class SceneManager():

    def make_scene(self):

        bpy.ops.mesh.primitive_plane_add(location=(0.0, 0.0, 0.0))
        floor = bpy.context.active_object
        floor.name = "Floor"
        mat = bpy.data.materials.new(name="FloorMaterial")
        floor.data.materials.append(mat)
        if version_ge_2_8:
            floor.material_slots[0].material.diffuse_color = (0.4, 0.5, 1.0, 1.0)
        else:
            floor.material_slots[0].material.diffuse_color = (0.4, 0.5, 1.0)

        if version_ge_2_8:
            bpy.ops.object.light_add(type='SUN', location=(1, 2, 2))
        else:
            bpy.ops.object.lamp_add(type='SUN', radius=1, location=(1.0, 1.0, 2.0))

        bpy.ops.object.camera_add(
            location=(1.5, -0.5, 1.15),
            rotation=(1.134, 0.0, 1.222),  # XYZ Euler
        )

        camera_name = bpy.data.cameras[-1].name
        self.camera = bpy.data.objects[camera_name]
        self.camera.scale = (0.2, 0.2, 0.2)

        self.scene = bpy.data.scenes[0]
        self.scene.camera = self.camera
        self.scene.render.resolution_x = 640
        self.scene.render.resolution_y = 480
        try:
            bpy.context.scene.cycles.device = 'GPU'
        except TypeError:
            pass

    def reset_blend(self):
        blnd.clear_all_objects()


class TestBasics(unittest.TestCase, SceneManager):

    def __init__(self):
        self._test_name = None

    def _update_test_name(self):
        self._test_name = tb.extract_stack(limit=2)[-2][2]

    def setUp(self):
        utils.try_rmtree(temp_dir)
        utils.try_makedirs(temp_dir)
        self.reset_blend()
        self.make_scene()
        self.panda = robot_driver.PandaIKDriver()

    def _flatten_test_results(self, timeout=60, sleep=1):
        t0 = time.time()
        for sub in os.listdir(temp_dir):

            sud_dir = osp.join(temp_dir, sub)
            if not osp.isdir(sud_dir):
                continue

            still_waiting = True
            while (time.time() - t0) < timeout and still_waiting:
                images = os.listdir(sud_dir)

                still_waiting = len(images) == 0
                if still_waiting:
                    time.sleep(sleep)
                    continue

                for f in images:
                    fname, fmt = f.split(".")
                    num = fname[5:]
                    src = osp.join(temp_dir, sub, f)
                    dst = osp.join(
                        test_out_dir,
                        ".".join((
                            self._test_name + "_" + num,
                            sub.lower(),
                            fmt,
                        )),
                    )
                    utils.try_move(src, dst)

    def tearDown(self):
        composite_node_material.set_materials(temp_dir)
        bpy.ops.render.render(write_still=True)
        self._flatten_test_results()
        composite_node_material.disable_nodes(self.scene)
        self._test_name = None

    def test_delete_panda(self):
        self._update_test_name()
        self.panda.delete()

    def test_composite_node_material(self):
        self._update_test_name()


class TestPandaIK(unittest.TestCase, SceneManager):

    def _update_test_name(self):
        self._test_name = tb.extract_stack(limit=2)[-2][2]

    def setUp(self):
        utils.try_rmtree(temp_dir)
        utils.try_makedirs(temp_dir)
        self.reset_blend()
        self.make_scene()
        self.panda = robot_driver.PandaIKDriver()

    def _flatten_test_results(self, timeout=20, sleep=1):
        _flatten_test_results_file(self._test_name, timeout=timeout, sleep=sleep)

    def tearDown(self):
        self.scene.render.filepath = temp_dir + "/image"
        bpy.ops.render.render(write_still=True)
        self._flatten_test_results()
        self._test_name = None

    def test_base_rotate__45deg(self):
        self._update_test_name()
        self.panda.base.rotate(45, Z_AXIS)

    def test_base_rotate_by_R__45deg(self):
        self._update_test_name()
        R = Matrix.Rotation(DEG2RAD * 45.0, 4, Z_AXIS)
        self.panda.base.rotate_by_R(R)

    def test_base_set_rotation_matrix__210deg(self):
        self._update_test_name()
        self.panda.base.set_rotation_matrix(210.0, Z_AXIS)

    def test_base_set_rotation_matrix_to_R__210deg(self):
        self._update_test_name()
        R = Matrix.Rotation(DEG2RAD * 210.0, 4, Z_AXIS)
        self.panda.base.set_rotation_matrix_to_R(R)

    def test_base_translate__up(self):
        self._update_test_name()
        self.panda.base.translate((-0.2, 0.0, 0.3))

    def test_base_set_position_under__floor(self):
        self._update_test_name()
        self.panda.base.set_position((0.0, -0.1, -0.4))

    def test_tcp_rotate__30deg(self):
        self._update_test_name()
        self.panda.tcp.rotate(30, X_AXIS)

    def test_tcp_set_rotation_matrix_to_R__45deg(self):
        self._update_test_name()
        R = Matrix.Rotation(DEG2RAD * 45.0, 4, Y_AXIS)
        self.panda.tcp.set_rotation_matrix_to_R(R)

    def test_tcp_translate__down(self):
        self._update_test_name()
        self.panda.tcp.translate((0.0, 0.0, -0.3))

    def test_tcp_set_position__up(self):
        self._update_test_name()
        self.panda.tcp.set_position((0.2, -0.2, 1.0))

    def test_gripper_open_by__valid(self):
        self._update_test_name()
        self.panda.gripper.open_by(0.3)

    def test_gripper_set_to__out_of_range(self):
        self._update_test_name()
        self.panda.gripper.set_to(-0.5)


class TestPandaFK(unittest.TestCase, SceneManager):

    def _update_test_name(self):
        self._test_name = tb.extract_stack(limit=2)[-2][2]

    def setUp(self):
        utils.try_rmtree(temp_dir)
        utils.try_makedirs(temp_dir)
        self.reset_blend()
        self.make_scene()
        self.panda = robot_driver.PandaFKDriver()

    def _flatten_test_results(self, timeout=20, sleep=1):
        _flatten_test_results_file(self._test_name, timeout=timeout, sleep=sleep)

    def tearDown(self):
        self.scene.render.filepath = temp_dir + "/image"
        bpy.ops.render.render(write_still=True)
        self._flatten_test_results()
        self._test_name = None

    def test_set_joint_angle__axis_5_90deg(self):
        self._update_test_name()
        self.panda.set_joint_angle(5, 90)

    def test_increment_joint_angle__axis_4_1rad(self):
        self._update_test_name()
        self.panda.increment_joint_angle(4, 1, deg=False)


def run_tests():
    test_suite_order = [
        TestBasics(),
        TestPandaIK(),
        TestPandaFK(),
    ]
    for tester in test_suite_order:
        suite = str(tester.__class__).split(".")[1].split("'")[0]
        print("== Starting Test-Suite: {}".format(suite))
        for method in dir(tester):
            if method[:5] == "test_":
                tester.setUp()
                getattr(tester, method)()
                tester.tearDown()
                print(". completed: {}".format(method))


if __name__ == '__main__':
    # TODO: test again once blender-as-module works out
    # might need to open file (instead of reset) in setUp
    unittest.main()
