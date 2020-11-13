# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

This folder contains some potentially useful scripts.

* **abrgen**: main script to call in order to commence rendering. Refer to the documentation.
* **abr_range2depth**: similarly to **abrgen** the script can be used to post process a dataset to convert range
  images to depth. This should be done automatically during rendering. However, we provide this also as a 
  separate option.
* **run_tests**: scripts dedicated to run tests. See the documentation.

The folder contains also additional support script that, most likely, standard users won't need.
However, in case of need a user can take inspiration from them.

These are:

* **sh**: directory with general .sh support scripts to e.g., set up appropriate environments to deploy rendering
  on a computational cluster.
* **slurm**: directory with scripts to generate .sh deployment scripts for clusters running SLURM as scheduler.
* **lsf**: similar to **slurm** but assuming LSF as scheduler.
