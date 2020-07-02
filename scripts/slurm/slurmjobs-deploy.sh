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

# Script to deploy all desired slurmbatch job
# Use in combination with generate_slurm_scripts.py

# required positional argument to select desired basename for config/slurmbatch.sh scripts
BASENAME=${1?Error: no BASENAME for slurmbatch .sh script to deploy given}
# optional (positional) argument to generate slurm bash scripts
GENSCRIPTS=${2:-False}
# optional (positional) argument to control clean-up after execution
CLEAN=${3:-False}
# optional (positional) argument to control deployment
DEPLOY=${4:-True}

# optional script generation
if [[ $GENSCRIPTS == "True" ]]; then

    # setup
    NAME=marco.todescato
    CFGBASENAME=$BASENAME
    CFGBASEPATH=$HOME/amira_blender_rendering/config
    PYENVNAME=blender
    CUDNN_VERSION=10.0_v7.3.1
    GPU=4
    CPU=4
    SSD=20
    RAM=32
    DAYS=2
    HH=0
    MM=0
    ABR=$HOME/amira_blender_rendering
    OUTPATH=/data/Employees/$USER/slurm_results
    conda activate $PYENVNAME
    echo "Generating (generate_slurm_scrpts.py) slurm bash scripts with following configuration values:"
    echo "User name:     $NAME"
    echo "cfg_base_name: $CFGBASENAME"
    echo "cfg_base_path: $CFGBASEPATH"
    echo "python env:    $PYENVNAME"
    echo "cudnn_version: $CUDNN_VERSION"
    echo "gpus:          $GPU"
    echo "cpus:          $CPU"
    echo "ssd:           $SSD"
    echo "ram:           $RAM"
    echo "dd-hh:mm       $DAYS-$HH:$MM"
    echo "abr_base_path: $ABR"
    echo "out_path:      $OUTPATH"

    # check for user
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
        --gpu $GPU \
        --cpu $CPU \
        --ssd $SSD \
        --ram $RAM \
        --dd $DAYS \
        --hh $HH \
        --mm $MM \
        --abr-path $ABR \
        --out-path $OUTPATH
    conda deactivate
fi

# deployment
if [[ $DEPLOY == "True" ]]; then
    echo ''
    for f in `ls ./tmp-slurmbatch-$BASENAME*.sh`; do
        echo "Deploying batch job: $f"
        sbatch  $f
    done
fi

# optional clearning
if [[ $CLEAN == "True" ]]; then
    echo ''
    echo "Cleaning up..."
    rm tmp-slurmbatch-$BASENAME*.sh
fi
