#!/bin/bash

# Script to deploy all desired slurmbatch job
# Use in combination with generate_slurm_scripts.py

BASENAME=${1?Error: no BASENAME for slurmbatch .sh script to deploy given}
GENSCRIPTS=${2:-False}
CLEAN=${3:-False}

# optional script generation
if [ $GENSCRIPTS = True ]; then
    # setup
    NAME=marco.todescato
    CFGBASENAME=$BASENAME
    CFGBASEPATH=$HOME/amira_blender_rendering/config/
    PYENVNAME=blender
    GPU=4
    CPU=4
    SSD=20
    RAM=32
    DAYS=1
    HH=0
    MM=0
    ABR=$HOME/amira_blender_rendering
    # generate slurm scripts
    conda activate $PYENVNAME
    echo "Generating (generate_slurm_scrpts.py) slurm bash scripts with following configuration values:"
    echo "User name:     $NAME"
    echo "cfg_base_name: $CFGBASENAME"
    echo "cfg_base_path: $CFGBASEPATH"
    echo "python env:    $PYENVNAME"
    echo "gpus:          $GPU"
    echo "cpus:          $CPU"
    echo "ssd:           $SSD"
    echo "ram:           $RAM"
    echo "dd-hh:mm       $DAYS-$HH:$MM"
    echo "abr_base_path: $ABR"
    python generate_slurm_scripts.py \
        $NAME \
        $CFGBASENAME \
        $CFGBASEPATH \
        $PYENVNAME \
        --gpu $GPU \
        --cpu $CPU \
        --ssd $SSD \
        --ram $RAM \
        --dd $DAYS \
        --hh $HH \
        --mm $MM \
        --abr-path $ABR
    conda deactivate
fi

# deployment
echo ''
for f in `ls ./slurmbatch-$BASENAME*.sh`; do
    echo "Deploying batch job associated to '$f'"
    sbatch  $f
done

# optional clearning
echo ''
if [ $CLEAN = True ]; then
    echo "Cleaning up..."
    rm slurmbatch-$BASENAME*.sh
fi
