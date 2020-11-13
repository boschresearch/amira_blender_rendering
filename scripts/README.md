This folder contains some potentially useful scripts. In particular:

* **abrgen**: main script to call in order to commence rendering. Refer to the documentation.
* **abr_range2depth**: similarly to **abrgen** the script can be used to post process a dataset to convert range
  images to depth. This should be done automatically during rendering. However, we provide this also as a 
  separate option.
* **run_tests**: scripts dedicated to run tests. See the documentation.

Also, it provides additional support scripts that, most likely, standard users won't need.
However, in case of need, one can take inspiration from them. These are:

* **sh**: directory with general .sh support scripts to e.g., set up appropriate environments to
  deploy rendering on a computational cluster.
* **slurm**: directory with scripts to generate .sh deployment scripts for clusters running SLURM
  as scheduler.
* **lsf**: similar to **slurm** but assuming LSF as scheduler.
