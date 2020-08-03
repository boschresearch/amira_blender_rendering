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

# Script to generate deployment scripts
# Use in combination with generate_slurm_scripts.py

# required positional argument to select desired basename for config/slurmbatch.sh scripts
BASENAME=${1?Error: no BASENAME for config and associated slurmbatch .sh script to deploy given}
BASEPATH=${2:-$HOME/amira_blender_rendering/config}

# setup
NAME=marco.todescato
CFGBASENAME=$BASENAME
CFGBASEPATH=$BASEPATH
PYENVNAME=blender
INPUT_FLAG=multiview
CUDNN_VERSION=10.0_v7.3.1
GPU=1
CPU=4
SSD=40
RAM=32
DAYS=2
HH=0
MM=0
ABR=$HOME/amira_blender_rendering
OUTPATH=/data/Employees/$USER/slurm_results
DSET_NAME=PandaTable-DoN
conda activate $PYENVNAME
echo "Generating (generate_slurm_scrpts.py) slurm bash scripts with following configuration values:"
echo "User name:     $NAME"
echo "cfg_base_name: $CFGBASENAME"
echo "cfg_base_path: $CFGBASEPATH"
echo "python_env:    $PYENVNAME"
echo "input_flag:    $INPUT_FLAG"
echo "cudnn_version: $CUDNN_VERSION"
echo "gpus:          $GPU"
echo "cpus:          $CPU"
echo "ssd:           $SSD"
echo "ram:           $RAM"
echo "dd-hh:mm       $DAYS-$HH:$MM"
echo "abr_base_path: $ABR"
echo "out_path:      $OUTPATH"
echo "dset_name:     $DSET_NAME"

# user check
echo -n "Continue? [Y/N]: "
read OK
if [[ $OK == "N" ]]; then
    echo "Aborting..."
    exit 0
fi

# generate scripts
python generate_slurm_scripts.py \
    $NAME \
    $CFGBASENAME \
    $CFGBASEPATH \
    $PYENVNAME \
    --cudnn $CUDNN_VERSION \
    --input-flag $INPUT_FLAG \
    --gpu $GPU \
    --cpu $CPU \
    --ssd $SSD \
    --ram $RAM \
    --dd $DAYS \
    --hh $HH \
    --mm $MM \
    --abr-path $ABR \
    --out-path $OUTPATH \
    --dset-name $DSET_NAME
conda deactivate

