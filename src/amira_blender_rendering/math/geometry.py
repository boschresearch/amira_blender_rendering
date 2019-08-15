#!/usr/bin/env python

import bpy
from mathutils import Vector, Euler

def project_p3d(p: Vector,
            camera: bpy.types.Object = bpy.context.scene.camera,
            render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """Project a point p onto the image plane of a camera. The returned value is
    in normalized device coordiantes. That is, left upper corner is -1,1, right
    bottom lower corner is 1/-1"""

    if camera.type != 'CAMERA':
        raise Exception(f"Object {camera.name} is not a camera")

    if len(p) != 3:
        raise Exception(f"Vector {p} needs to be 3 dimensional")

    # get model-view and projection matrix
    depsgraph  = bpy.context.evaluated_depsgraph_get()
    modelview  = camera.matrix_world.inverted()
    projection = camera.calc_matrix_camera(
            depsgraph,
            x=render.resolution_x,
            y=render.resolution_y,
            scale_x=render.pixel_aspect_x,
            scale_y=render.pixel_aspect_y)

    # project point (generastes homogeneous coordinate)
    p_hom = projection @ modelview @ Vector((p.x, p.y, p.z, 1))

    # normalize to get projected point
    p_proj = Vector((p_hom.x/p_hom.w, p_hom.y/p_hom.w))
    return p_proj


def p2d_to_pixel_coords(p: Vector,
        render: bpy.types.RenderSettings = bpy.context.scene.render) -> Vector:
    """Take a 2D point in normalized device coordiantes to pixel coordinates
    using specified render settings"""

    if len(p) != 2:
        raise Exception(f"Vector {p} needs to be 2 dimensinoal")

    return Vector(((render.resolution_x - 1) * (p.x+1.0) / +2.0,
                   (render.resolution_y - 1) * (p.y-1.0) / -2.0))


def get_relative_rotation(obj1: bpy.types.Object,
        obj2: bpy.types.Object = bpy.context.scene.camera) -> Euler:

    """Get the relative rotation between two objects in terms of the second
    object's coordinate system. Note that the second object will be default
    initialized to the scene's camera.

    Returns:
        Euler angles given in radians
    """

    obj1_m = obj1.rotation_euler.to_matrix()
    obj2_m = obj2.rotation_euler.to_matrix()
    rel_rotation_m = (obj1_m.inverted() @ obj2_m)
    rel_rotation_e = rel_rotation_m.to_euler()
    return rel_rotation_e


def get_relative_translation(obj1: bpy.types.Object,
        obj2: bpy.types.Object = bpy.context.scene.camera) -> Vector:
    """Get the relative translation between two objects in terms of the second
    object's coordinate system. Note that the second object will be default
    initialized to the scene's camera.

    Returns:
        3D Vector with relative translation (in OpenGL coordinates)
    """

    # get vector in world coordinats and rotate into object cordinates
    v = obj1.location - obj2.location
    rot = obj2.rotation_euler.to_matrix()
    return rot.inverted() @ v


def get_relative_transform(obj1: bpy.types.Object,
        obj2: bpy.types.Object = bpy.context.scene.camera):
    """Get the relative transform between obj1 and obj2 in obj2's coordinate
    frame."""

    t = get_relative_translation(obj1, obj2)
    r = get_relative_rotation(obj1, obj2)
    return t, r



if __name__ == "__main__":
    obj = bpy.data.objects['Tool.Cap']
    cam = bpy.context.scene.camera
    render = bpy.context.scene.render

    print(obj.location)
    vs = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    print(vs)
    ps = [project_p3d(v, cam) for v in vs]
    print(ps)
    pxs = [p2d_to_pixel_coords(p) for p in ps]
    print(pxs)
    oks = [px[0] >= 0 and px[0] < render.resolution_x and px[1] >= 0 and px[1] < render.resolution_y for px in pxs]
    print(oks)
    print(all(oks))

