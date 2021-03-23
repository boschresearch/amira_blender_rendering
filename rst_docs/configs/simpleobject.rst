.. highlight:: ini

Simple Object Scenario
=======================

The Simple Object Scenario represent a prototypical scenario of the
simplest type implemented in ABR.

For an more in depth tutorial on how to set up a very simple custom scenario
refer to :ref:`Set Up a Simple Custom Scenario`

Most of the following configurations are common to other scenarios.
Hence, please refer to :ref:`Base Configuration` for an overview.

For the SimpleObject scenario refer to the config file config/examples/single_object_toolcap_example.cfg

.. code-block::

    [dataset]
    # In this section we specify basic properties of the dataset

    # Specify how many images should be rendered
    image_count = 5

    # Specify the base path where data will be written to. Note that,
    # differently to more complex scenarios, e.g., see :ref:`Workstation Scenarios`,
    # here there is only one configuration and one camera.
    # Hence hence the base path coincides with the location where data are actually written.
    base_path = $AMIRA_DATASETS/SimpleToolCap-Train

    # specify the scene type
    scene_type = SimpleObject


    [camera_info]
    # In this section we specify camera specific configurations.

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
    intrinsic = 9.9801747708520452e+02,9.9264009290521165e+02,6.6049856967197002e+02,3.6404286361152555e+02,0

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
    samples = 8

    [scene_setup]
    # we also specify where to load environment textures from
    #
    # For this simple case, this is the only scene-specific configuration value
    environment_textures = $AMIRA_DATASETS/OpenImagesV4/Images

    [parts]
    # here we use the 'ply only' version to load objects. Fore more documentation,
    # see config/workstation_scenario01_test.cfg
    ToolCap =

    # this scene loads a tool cap mesh. This is loaded from the corresponding mesh
    ply.ToolCap = $AMIRA_DATA_GFX/cad/parts/tool_cap_x10.ply

    # ply models often have a different scale than what is used in blender. Here, we
    # have to scale down the model to match blender units (which are treated to be
    # meters)
    ply_scale.ToolCap = 0.001, 0.001, 0.001

    # another single object to try
    LetterB =
    ply.LetterB = $AMIRA_DATA_GFX/cad/parts/B.ply
    ply_scale.LetterB = 0.001, 0.001, 0.001

    [scenario_setup]
    # here we specify the objects of interest. In the case of this demo, we are only
    # interested in one part of type "tool_cap". Although this configuration option
    # is not used in the backend script, it is useful to document the items that are
    # part of the scenario
    target_object = ToolCap
    object_material = metal
