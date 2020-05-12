Directory and File Format Specification
=======================================

Every dataset rendered using ABR follows the same folder and annotation structure.
In the following we describe them both.

Output Folder Structure
-----------------------
Every dataset rendered, e.g., by running

.. code-block:: bash

   $ abrgen --config path/to/config.cfg

follows the same folder structure. Assuming that 

.. code-block:: 

    [dataset]
    base_path = RootDir/BaseName

    [scene_setup]
    cameras = Camera  # only frontal view (mono) camera

it consists of the following

+ RootDir/
|
|--+ BaseName.Camera
|  |-- Dataset.cfg: summary configuration for rendered dataset
|  |
|  |--+ Images/
|  |  |-- backdrop/ : folder with background drop images (composite mask)
|  |  |-- depth/    : folder with depth images
|  |  |-- maks/     : folder with mask for each segmented object
|  |  |-- rgb/      : folder with RGG images
|  |
|  |--+ Annotations/
|  |  |-- OpenCV/ : annotations with object poses expressed in OpenCV convention (see annotation file content)
|  |  |-- OpenGL/ : annotations with object poses expressed in OpenGL convention (see annotation file content)

Annotation (.json) File Contents
--------------------------------

