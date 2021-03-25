
## PandaTable Scenario

The pandatable scenarion has the following options that you can set in a
corresponding configuration file. For an example of configuration files that
were used, have a look at `config/pandatable_example.cfg`.

```python
[dataset]
# Specify how many images should be rendered
image_count = 5
# Specify the base path where data will be written to.
base_path = $AMIRA_DATASETS/PandaTable-Train
# specify the scene type
scene_type = PandaTable

[camera_info]
# In this section you specify the camera information, which will have a direct
# impact on rendering results.

# The width and height have an influence on the rendering resolution. In case
# you wish to set a specific calibration matrix that you obtained, for
# instance, from OpenCV, and do not wish to temper with the rendering
# resolution, then set these values to 0.
width = 640
height = 480

# The camera model to use. At the moment, this value is ignored in
# amira_blender_rendering. However, because all rendering is in fact done with a
# pinhole camera model, this value serves as documentation
model = pinhole

# Also this value has no impact on rendering likewise the model. However, if
# you want to specify a certain camera name for documentation purposes, this is
# the place.
name = Pinhole Camera

# You can specify the intrinsic calibration information that was determined for
# a camera, for instance with OpenCV.
#
# Here, we use the format
#   intrinsics = fx, fy, cx, cy
# Where the fx, fy values represented focal lengths, and cx, cy defines the
# camera's principal point.
#
# You can extract fx, fy, cx, cy from a calibration matrix K:
#
#         fx  s   cx
#    K =   0  fy  cy
#          0  0   1
#
# Note, however, that the values in your calibration matrix or intrinsics
# specification might not end up in proper render resolutions. For instance,
# this is the case in the example below, which would result in a rendering
# resolution of about 1320.98 x 728.08.  Blender will round these values to
# suitable integer values.  As a consequence, even if you set width and height
# above to 0, the effective intrinsics that blender uses might be slightly
# different from your K.
#
# To accomodate this 'issue', amira_blender_rendering will write a value
# 'effective_intrinsics' to the configuration as soon as setting up cameras and
# rendering is done. Recall that all configurations will be stored alongside the
# created dataset, so you can easily retrieve the effective_intrinsics in
# downstream applications
intrinsics = 9.9801747708520452e+02,9.9264009290521165e+02,6.6049856967197002e+02,3.6404286361152555e+02,0

# zeroing angles rx, ry, rz in deg to account for camera non-zero default rotation
zeroing = 0, 0, 0

[render_setup]
# specify which renderer to use. Usually you should leave this at
# blender-cycles. Note that, at the moment, this is hard-coded to cycles
# internally anyway.
backend = blender-cycles
# integrator (either PATH or BRANCHED_PATH)
integrator = BRANCHED_PATH
# use denoising (true, false)
denoising = True
# samples the ray-tracer uses per pixel
samples = 64
# allow occlusions of target objects (true, false)
allow_occlusions = False

[scene_setup]
# specify the blender file from which to load the scene
blend_file = $AMIRA_DATA_GFX/modeling/robottable_empty.blend
# specify where background / environment images will be taken from during
# rendering. This can be a single file, or a directory containing images
environment_texture = $AMIRA_DATASETS/OpenImagesV4/Images
# specify which cameras to use for rendering. The names here follow the names in
# the blender file, i.e. Camera, StereoCamera.Left, StereoCamera.Right
cameras = Camera
# cameras = Camera, StereoCamera.Left, StereoCamera.Right
# number of frames to forward-simulate in the physics simulation
forward_frames = 15

[parts]
# This section allows you to add parts from separate blender or PLY files. There
# are three different ways for specification
#
# 1) blender only
#   you need to specify a name of an object, and a blender file in
#   which the object resides in the format
#       part_name = blend_file
#
#   Example:
#       hammerschraube = $AMIRA_DATA_GFX/cad/rexroth/hammerschraube.blend
#
#   Note: If no further configs are set, the object name *must* correspond 
#   to the name that the object has in the blender file. 
#   They will be loaded on-demand when setting up the scenario.
#   Loading objects from the same .blend file but with different names is
#   possible by using the `name.part_name` tag.
#   This might be useful in case you want to load the same object but with
#   different scale factors (see below for the use of blend_scale).
#
#   Example:
#       my_cool_name = $AMIRA_DATA_GFX/cad/rexroth/hammerschraube.blend
#       name.my_cool_name = hammerschraube
#
#   The `name.part_name` tag *must* correspond to the name the object has in the
#   blender file. After loading, the object name will be overwritten by `my_cool_name`.  
#
# 2) blender + PLY
#   This variant is useful when you want to use the dataset later on and need
#   information about the origin of the blender model.
#   For instance, you might have access to a specific CAD model, and you want to
#   train a deep network to detect this CAD model. Such a network might require
#   more information from the CAD model to work. However, you probably do not
#   wish to load a blender file, but the (simpler) PLY file during network
#   training. Given that this configuration is stored alongside the generated
#   dataset, the information is in one place.
#   Note that, often, PLY CAD Models have a different scaling than blender
#   models. While blender defaults to using 1m, CAD software often defaults to
#   using mm or cm. Hence, you also need to specify a scale factor
#
#   The format to specify the ply-file and scale factor is:
#       ply.part_name = path/to/ply
#       ply_scale.part_name = 1.0, 1.0, 1.0
#
#   Where the scale is a vector, consisting of the scaling in X, Y, and Z
#   dimensions.
#
#   Example:
#       hammerschraube = $AMIRA_DATA_GFX/cad/rexroth/hammerschraube.blend
#       ply.hammerschraube = $AMIRA_DATA_PERCEPTION/CADModels/rexroth/
#       ply_scale.hammerschraube = 0.001, 0.001, 0.001
#
#   However we also allow to scale objects loaded directly from .blend files.
#   For this, use the correpsonding `blend_scale.part_name` config tag.
#
# 3) PLY only
#   In case you only have access to a PLY file, you can specify everything
#   according to the aforementioned items but leave the blender path empty.
#
#   Example:
#       hammerschraube =
#       ply.hammerschraube = $AMIRA_DATA_PERCEPTION/CADModels/rexroth/
#       scale.hammerschraube = 0.001, 0.001, 0.001
#
#   Important: Do *not* forget to add 'part_name =', despite not giving a
#   blender path name. This name will be required if you want to specify the
#   target_objects below
#
# Note: Make sure that in your blender files the parts are active rigid objects with
#       proper weight and sensitivity margin!
#
# Note/Attenton: We will not automatically add rigid body dynamics to ply-only models!
#               This means that if not actively added, the object will (by default) be
#               regarded as passive object (i.e., w/o rigid-body properties), hence not
#               subject to the dynamic simulation.
# 
# ATTENTION: when scaling objects the final behavior might be different between
#            loading objects from .blend or from .ply since the intrinsic scales might
#            be different within the two files.

# The first example is a "hammerschraube" (hammer head screw)
hammerschraube = $AMIRA_DATA_GFX/cad/rexroth/hammerschraube.blend
ply.hammerschraube = $AMIRA_DATA_GFX/cad/rexroth/hammerschraube.ply
ply_scale.hammerschraube = 0.001

# The second example is a 60x60 angle element.
winkel_60x60 = $AMIRA_DATA_GFX/cad/rexroth/winkel_60x60.blend
ply.winkel_60x60 = $AMIRA_DATA_GFX/cad/rexroth/winkel_60x60.ply
ply_scale.winkel_60x60 = 0.001

# this is a star knob
sterngriff = $AMIRA_DATA_GFX/cad/rexroth/sterngriff.blend
ply.sterngriff = $AMIRA_DATA_GFX/cad/rexroth/sterngriff.ply
ply_scale.sterngriff = 0.001

# a cube-like connection
wuerfelverbinder_40x40 = $AMIRA_DATA_GFX/cad/rexroth/wuerfelverbinder_40x40.blend
ply.wuerfelverbinder_40x0 = $AMIRA_DATA_GFX/cad/rexroth/wuerfelverbinder_40x40_3.ply
ply_scale.wuerfelverbinder_40x40 = 0.001

# a flanged nut
bundmutter_m8 = $AMIRA_DATA_GFX/cad/rexroth/bundmutter_m8.blend
ply.bundmutter_m8 = $AMIRA_DATA_GFX/cad/rexroth/bundmutter_m8.ply
ply_scale.bundmutter_m8 = 0.001

# it is also possible to load objects from the same blend file
# but using a different class name. This will be treated as different
# objects in the annotations. Useful for e.g., loading same objects
# with different scales
bundmutter_m8_A = $AMIRA_DATA_GFX/cad/rexroth/bundmutter_m8.blend
name.bundmutter_m8_A = bundmutter_m8
blend_scale.bundmutter_m8_A = 0.7

# similarly we can do with ply files. In this case, it is not
# necessary to define a source name with the `name` tag since
# when loading from PLY we are not binded to object names
bundmutter_m8_B =
ply.bundmutter_m8_B = $AMIRA_DATA_GFX/cad/rexroth/bundmutter_m8.ply
ply_scale.bundmutter_m8_B = 0.003

# object 01 from the T-Less dataset
tless_obj_01 = $AMIRA_DATA_GFX/cad/tless/blender/obj_01.blend
ply.tless_obj_01 = $AMIRA_DATA_GFX/cad/tless/models/obj_01.ply
ply_scale.tless_obj_01 = 0.001

# object 06 from the T-Less dataset
tless_obj_06 = $AMIRA_DATA_GFX/cad/tless/blender/obj_06.blend
ply.tless_obj_06 = $AMIRA_DATA_GFX/cad/tless/models/obj_06.ply
ply_scale.tless_obj_06 = 0.001

# object 06 from the T-Less dataset
tless_obj_13 = $AMIRA_DATA_GFX/cad/tless/blender/obj_13.blend
ply.tless_obj_13 = $AMIRA_DATA_GFX/cad/tless/models/obj_13.ply
ply_scale.tless_obj_13 = 0.001

[scenario_setup]
# Specify all target objects that shall be dropped at random locations into the
# environment. Target objects are all those objects that are already in the
# .blend file in the 'Proto' collection. You can also specify parts that were
# presented above using the syntax 'parts.partname:count'
target_objects = parts.sterngriff:4, parts.wuerfelverbinder_40x40:3, parts.hammerschraube:7, parts.winkel_60x60:5
# Similarly we allow to select additional objects to drop in the environment for which
# annotated information are NOT stored, i.e., they serve as distractors
distractor_objects = []

# Camera multiview is applied to all cameras selected in scene_setup.cameras and
# it is activated calling abrgen with the --render-mode multiview flag.
# For specific multiview modes/configs config refer to "Multiview Configuration" docs.
[multiview_setup]
# control how multiview camera locations are generated (bezier curve, circle, viewsphere etc.)
mode =
# mode specific configuration
mode_config =

# additional debug configs (used is debug.enable=True)
[debug]
# if in debug mode (see baseconfiguration), produce temporary plot of camera locations (best for multiview rendering)
plot = False
# if in debug mode (see baseconfiguration), plot coordinate axis system for camera
# poses in before multiview rendering
plot_axis = False
# if in debug mode (see baseconfiguration), toggle scatter plot of camera locations
# before multiview rendering 
scatter = False
# if in debug mode (see baseconfiguration), enable saving to blender.
# The option can be used to e.g., inspect whether multiple camera locations are occluded,
# check object occlusions, check the dymanic simulation.
save_to_blend = False
```