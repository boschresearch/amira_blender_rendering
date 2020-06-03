#!/bin/bash

# Script to deploy all desired slurmbatch job
# Use in combination with generate_slurm_scripts.py

# required positional argument to select desired basename for config/slurmbatch.sh scripts
BASENAME=${1?Error: no BASENAME for lsfbatch .sh script to deploy given}
# optional (positional) argument to generate slurm bash scripts
GENSCRIPTS=${2:-False}
# optional (positional) argument to control clean-up after execution
CLEAN=${3:-False}
# optional (positional) argument to control deployment
DEPLOY=${4:-True}

# optional script generation
if [[ $GENSCRIPTS == "True" ]]; then

    # setup
    CFGBASENAME=$BASENAME
    CFGBASEPATH=$HOME/amira_blender_rendering/config
    PYENVNAME=blender
    CUDNN_VERSION=10.1_v7.6
    CONDA_VERSION=4.4.8-readonly
    GPU=2
    GPU_TYPE=rb_regular
    JOB_SLOTS=1
    CPU=4
    RAM=4
    HH=24
    MM=0
    AMIRA_STORAGE=/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA
    ABR=$HOME/amira_blender_rendering
    HEAVY_DUTY_DIR=$HOME/lsf_results
    OUT_DIR=/fs/scratch/rng_cr_bcai_dl/$USER/lsf_results
    source activate $PYENVNAME
    echo "Generating (generate_slurm_scrpts.py) slurm bash scripts with following configuration values:"
    echo "cfg_base_name:  $CFGBASENAME"
    echo "cfg_base_path:  $CFGBASEPATH"
    echo "python env:     $PYENVNAME"
    echo "cudnn_version:  $CUDNN_VERSION"
    echo "conda_version:  $CONDA_VERSION"
    echo "gpus:           $GPU"
    echo "gpu_type:       $GPU_TYPE"
    echo "job_slots:      $JOB_SLOTS"
    echo "cpus:           $CPU"
    echo "ram:            $RAM"
    echo "hh:mm           $HH:$MM"
    echo "amira_storage:  $AMIRA_STORAGE"
    echo "abr_base_path:  $ABR"
    echo "heavy_duty_dir: $HEAVY_DUTY_DIR"
    echo "out_dir:        $OUT_DIR"

    # check for user
    echo -n "Continue? [Y/N]: "
    read OK
    if [[ $OK == "N" ]]; then
        echo "Aborting..."
        exit 0
    fi

    # generate scripts
    python generate_lsf_scripts.py \
        $CFGBASENAME \
        $CFGBASEPATH \
        $PYENVNAME \
	    --cudnn $CUDNN_VERSION \
        --conda $CONDA_VERSION \
        --gpu $GPU \
        --gpu-type $GPU_TYPE \
        --job-slots $JOB_SLOTS \
        --cpu $CPU \
        --ram $RAM \
        --hh $HH \
        --mm $MM \
        --amira-storage $AMIRA_STORAGE \
        --abr-path $ABR \
        --heavy-duty-dir $HEAVY_DUTY_DIR \
        --out-dir $OUT_DIR
    source deactivate
fi

# deployment
if [[ $DEPLOY == "True" ]]; then
    echo ''
    for f in `ls ./tmp-lsfbatch-$BASENAME*.sh`; do
        echo "Deploying batch job: $f"
        sbatch  $f
    done
fi

# optional clearning
if [[ $CLEAN == "True" ]]; then
    echo ''
    echo "Cleaning up..."
    rm tmp-lsfbatch-$BASENAME*.sh
fi
