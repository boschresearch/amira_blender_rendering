.. highlight:: ini

Overview
========

Nested INI Files
----------------

The ABR pipeline is configured using nested ini files. Nested ini files look
exactly like regular ini files, but allow for nested namespaces.

For instance, the following code example

.. code-block::

    [namespace]
    subnamespace.one = 1
    subnamespace.two = 2
    subnamespace.three = 3

is identical to

.. code-block::

    [namespace.subnamespace]
    one = 1
    two = 2
    three = 3

Although this disallows '.' in identifiers, this is practical when information
needs to be grouped in certain ways.

For instance, loading additional parts and objects into scenarios makes use of
nested namespaces for documentation purposes. You might want to add a certain
part or object from a blender file such that you can specify textures or
material properties directly within blender. However, your downstream
application such as a deep network for pose estimation only understands PLY
files and does not care about material properties. However, PLY files often use
a scaling, e.g. in mm, that is different from what you might use in blender,
e.g. m. To group all of this information, we make use of the following canonical
way to describe parts that we load from an ini file:

.. code-block::

    [parts]
    partname = /path/to/partname.blend
    ply.partname = /path/to/partname.ply
    ply_scale.partname = 0.010

Note that some configuration files, such as the WorkstationScenario
configuration, allow additional/extended specifications. Details about these are
described in their corresponding documentation.


Setting configuration paramters on the command line
---------------------------------------------------
Each (documented) configuration parameter can be set on the commandline. This is
useful if you want to briefly test a setting before rendering thousands of
images. For instance the Base Configuration argument ``dataset.image_count``,
which informs about how many images ABR shall render, can be set on the command
line by

.. code-block:: bash

   $ blender -b -P scripts/render_dataset.py -- --dataset.image_count 2
TOOD: update command?
