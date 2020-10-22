#!/bin/bash

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

# Script to deploy scripts

# required positional argument to select desired basename for config/slurmbatch.sh scripts
BASENAME=${1?Error: no BASENAME for config and associated slurmbatch .sh script to deploy given}

echo ''
for f in `ls ./$BASENAME*.sh`; do
    echo "Deploying batch job: $f"
    sbatch  $f
done
