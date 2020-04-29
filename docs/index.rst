.. amira_blender_rendering documentation master file, created by
   sphinx-quickstart on Wed Apr 22 09:17:29 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _blender: https://www.blender.org


Welcome to AMIRA Blender Rendering (ABR)'s documentation!
=========================================================

ABR is a pipeline for rendering large photo-realistic datasets, and is built
around blender_. By using blender_ to model scenes, we allow users to address
their specific requirements with respect to scenarios and model properties with
capabilities of a major and free 3D creation suite. Afterwards, ABR can be used
to handle generation of large amounts of photo-realistic data, for intance to
train deep networks for object recognition, segmentation, pose estimation, etc.

Note that, currently, ABR is operated mostly from the command line. The primary
reason for this is that ABR's intended purpose is also to be used on headless
GPU clusters or rendering farms.

Workflow
--------

The workflow of using ABR is held as simple as possible.

1. First, in blender_, you either develop your own scenario for which you would
   like to generate a dataset or adapt one of the existing scenarios.
2. If you decided on your own scenario, or if you heavily modified an existing
   scneario, you might need to provide what we call a `scenario backend` which
   will take care of setting up the file. For instance, you might wish to
   randomize object locations in every rendered image.
3. Next, you need to specify rendering information such as camera calbiration
   data or the number of images you would like to obtain in a `Configuration`
   (see :doc:`configs/overview`).
4. Finally, you commence dataset generation by running ``abrgen``.

Find out more about how to use ABR in :doc:`using`.


Citing ABR
----------
If you use ABR or the PhIRM dataset, please make sure to cite our work.

.. code-block:: latex

   @article{phirm2020,
       authors={},
       title={},
       year={},
       conference={},
       pages={}
   }



.. toctree::
   :maxdepth: 3
   :Caption: ABR User's Guide:

   installation.rst
   using.rst
   formats.rst
   datasets.rst
   fqa.rst
   troubleshooting.rst
   license.rst

.. toctree::
   :maxdepth: 3
   :Caption: ABR Developer's Guide:

   contributing.rst
   extending.rst

.. toctree::
   :maxdepth: 3
   :caption: Configurations:

   configs/overview.rst
   configs/baseconfiguration.rst
   configs/workstation_scenarios.rst
   configs/simpletoolcap.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
