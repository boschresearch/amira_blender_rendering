#!/bin/sh

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

# check env variables
if [ -z "$AMIRA_DATA" ];
then
    echo "ERROR: Environment variable AMIRA_DATA is not set."
    exit 1
fi

##
## The Real Deal ™
##
echo "Setting up rendering environment. This might take some time..."

# necessary env variables. used to grab data from
AMIRA_STORAGE=/data/Students/AMIRA/datasets
AMIRA_DATA_GFX_GIT=ssh://git@sourcecode.socialcoding.bosch.com:7999/amira/amira_data_gfx.git

# create directory structure
mkdir -p $AMIRA_DATA

# copy/extract datasets
git clone --quiet $AMIRA_DATA_GFX_GIT $AMIRA_DATA/amira_data_gfx
tar -C $AMIRA_DATA -xf $AMIRA_STORAGE/OpenImagesV4.tar
# fix wrong directory name
mv $AMIRA_DATA/OpenImageV4 $AMIRA_DATA/OpenImagesV4

echo "Ready to start rendering"
