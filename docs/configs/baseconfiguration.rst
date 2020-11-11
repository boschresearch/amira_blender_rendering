.. highlight:: ini

Base Configuration
==================

The base configuration is supported by all scenarios. It consists of several
namespaces, which are described in detail below.

dataset
-------
The ``dataset`` namespace contains information about a dataset such as number of
images, as well as the output directory where data will be written to.


.. code-block::

    [dataset]
    # Specify how many images should be rendered
    image_count = 5
    # Specify the base path where data will be written to. Note that this is a base
    # path, to which additional information will be added such as Scenario-Number
    # and Camera-Name
    base_path = $AMIRA_DATASETS/WorkstationScenarios-Train
    # specify the scene type
    scene_type = WorkstationScenarios


camera_info
-----------

Camera information is placed in the ``camera_info`` namespace. It contains
settings for image width and height, as well as (optional) intrinsic camera
information.

.. code-block::

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
    
    # A default camera in blender with 0 rotation applied to its transform looks
    # along the -Z direction. Blender's modelling viewport, however, assumes that
    # the surface plane is spanned by X and Y, where X indicates left/right. This
    # can be observed by putting the modelling viewport into the front viewpoint
    # (Numpad 1). Then, the viewport looks along the Y direction.
    #
    # As a consequence, the relative rotation between a camera image and an object
    # is only 0 when the camera would look onto the top of the object. Note that
    # this is rather unintuitive, as most people would expect that the relative
    # rotation is 0 when the camera looks at the front of an object.
    #
    # To accomodate for this, users can set their preferred 'zeroing' rotation 
    # by using the following configuration parameter encoding rotations 
    # around x, y and z-axis, respectively, in degrees.
    #
    # As an example, a value of 90, 0, 0 will apply a rotation of 90[deg] around x
    # when computing the relative rotation between the camera and an object in the
    # in the camera reference frame.
    zeroing = 0.0, 0.0, 0.0

render_setup
------------

The ``render_setup`` namespace is used to configure how blender's render backend
behaves, or which render backend to use.

.. code-block::

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

debugging
---------

The ``debug`` namespace can be used to toggle debug functionatilies.
For scene specific flags refer to the desider scene.

.. code-block::

    [debug]
    # activate debug logs and print-outs (true, false)
    enabled = False

postprocess
-----------

The ``postprocess`` namespace can be used to implement functionatilies
during postprocess and/or after the rendering phase

.. code-block::

    [postprocess]
    # our rendering pipeline exploits a perfect pinhole camera model according
    # to which points on a plane parallel to the image plane have different depth
    # values, computed as the disctance to the pin hole.
    # Conversely, standard raster models assume that points on planes parallel to
    # the image plane have all the same depth.
    # In this case, rectify_depth (true, false) adjst the depth values accordingly.
    rectify_depth = False
    # if rectify_depth is active, ovewrite depth files or store as separate (true, false)
    overwrite = Fasle
