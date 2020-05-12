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

| RootDir/
|  └── BaseName.Camera
|    ├── Dataset.cfg: summary configuration for rendered dataset
|    ├── Images/
|    |  ├── backdrop/ : folder with background drop images (composite mask)
|    |  ├── depth/    : folder with depth images
|    |  ├── masks/     : folder with mask for each segmented object
|    |  └── rgb/      : folder with RGG images
|    └── Annotations/
|       ├── OpenCV/ : :ref:`annotations<Annotations>` with object poses in OpenCV convention
|       └── OpenGL/ : :ref:`annotations<Annotations>` with object poses in OpenGL convention

Image indexing
--------------

All image files (except for masks) are named based on their index from 0 to N-1,
being N the total number of available images in the dataset.

In order to distinguish different instances of objects as well as different object types,
for masks we use the different convention n_t_i.png where:

* n : image number
* t : index for the object type
* i : instance number for the same object type


.. _Annotations:

Annotation File Contents
--------------------------------

Annotations are stored as .json files following the same naming convention used for images.
That is to image n.png corresponds the annotation n.json, being n the image number.

Each annotation file contains information about all the objects present in the scene in the form
of a list of dictionaries where each dictionary refer to one object instance.

Specifically, for each object we store:

* model_name  (str): label/name for object type
* model_id    (int): object type
* object_name (str): instance name
* object_id   (int): instance number for object of same type
* mask_name   (str): mask suffix
* pose (dict): dictionary containing:

  * q (list (4,)): rotation embedded as a quaternion (xyzw)
  * t (list (3,)): translation vector

* bbox (dict): dictionary containing bounding boxes information:

  * corners2d (list (2,2)): 2d bounding box corners in pixel space
  * corners3d (list (9,2)): 3d bounding box corners in (sub)pixel space 
  * aabb (list (9,3)): axis aligned bounding box corners in 3D space
  * oobb (list (9,3)): object oriented bounding box corners in 3D space
