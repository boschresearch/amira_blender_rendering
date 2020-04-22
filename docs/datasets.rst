Datasets
========

ABR's main purpose is to render datasets. For instance, we used it to render the
PhIRM dataset, which consists of several scenarios. They are described in more
detail below.

If you also rendered a dataset and made it publicly available, please drop us a
note and a description of the dataset. We will then add it to the list of
datasets and descriptions below.


PhIRM
-----

The PhIRM dataset consists of images of objects in an assembly / production
environment. Such environments usually have good but multiple lights, assembly
conveyers, as well as boxes in which parts lie. We did not model the environment
in excessive detail, but made sure that the environment looks similar to a tidy
and clean work environment.

Future extensions of the PhIRM dataset might include strongly cluttered
environments and bad light conditions.

TODO: image of the workstation scenarios

Objects
~~~~~~~

The PhIRM dataset contains rendered images for the following objects.

+------------------------+--------------+
| Object Name            | Reference ID |
+========================+==============+
| bundmutter_m8          | 0            |
+------------------------+--------------+
| hammerschraube         | 1            |
+------------------------+--------------+
| karabinerhaken         | 2            |
+------------------------+--------------+
| sterngriff             | 3            |
+------------------------+--------------+
| strebenprofil_20x20    | 4            |
+------------------------+--------------+
| winkel_60x60           | 5            |
+------------------------+--------------+
| wuerfelverbinder_40x40 | 6            |
+------------------------+--------------+

In addition, we rendered objects 06, 13, 20, and 27 from the T-Less dataset.


Scenarios
~~~~~~~~~

The firm dataset consists of 6 different `scenarios`, numbered from 0 to 5, each
only slightly different from the other. For instance, while one scenario might
be an empty table, another might have boxes in the environment as well.


Configurations
~~~~~~~~~~~~~~

We rendered 6 different configurations:

+------+--------------------------------------------------------+
| Code | Description                                            |
+------+--------------------------------------------------------+
| A    | single PhIRM object, single instance                   |
+------+--------------------------------------------------------+
| B    | single PhIRM object, multiple instances                |
+------+--------------------------------------------------------+
| C    | two PhIRM objects, two instances per object            |
+------+--------------------------------------------------------+
| D    | three PhIRM objects, three intances per object         |
+------+--------------------------------------------------------+
| E    | all PhIRM objects, multiple instances                  |
+------+--------------------------------------------------------+
| F    | T-Less Objects 06, 13, 20, 27, multiple instances each |
+------+--------------------------------------------------------+


PhIRM Folder Name Format
~~~~~~~~~~~~~~~~~~~~~~~~

The folder naming scheme for the PhIRM dataset follows from

.. code-block::

   WorkstationScenarios-{Configuration Code}_s{Scenario ID}_o{Object IDs}-{Camera}

w

Example:

A_s0_o0
A_s0_o1


**Note:** The Directory Reference ID
