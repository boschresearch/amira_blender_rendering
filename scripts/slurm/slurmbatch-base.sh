#!/bin/bash

# for more information about the content of this file, see the files
# in the directory $SLURMTEMPLATE on the GPU cluster

# to run this as a batch job, delete the first # in front of the following
# lines. Note that slurm commands are prefixed with #SBATCH (including the #)

# name of this batch job
#SBATCH --job-name=BlenderRenderJob

# account to which the resources get accounted to
#SBATCH --account=r31

# output configuration
#SBATCH --output=/home/%u/slurm_out/%x.%j.out
#SBATCH --error=/home/%u/slurm_out/%x.%j.err

# GPU, CPU, MEM configuration
#SBATCH --gres=gpu:4,ssd:20G
#SBATCH --cpus=4
#SBATCH --mem=20G

# Mail notifications
#SBATCH --mail-user=name.surname@de.bosch.com
#SBATCH --mail-type=begin,end,fail,time_limit_50,time_limit_80,time_limit_90

# maximum time configuration. format: "DAYS-HH:MM:SS", "DAYS-HH", or "HH:MM:SS"
#SBATCH --time "1-00"

# exit on error
set -e

# --- Step 0 --- prepare the environment, and go to the correct folder
echo "System setup"
module load slurm
module load cudnn/9.2_v7.2
source activate blender-env
cd /home/$USER/amira_blender_rendering
[ -d $SSD/tmp ] || mkdir $SSD/tmp

AMIRA_DATA=$HDD/data/

# --- Step 1 --- copy files
AMIRA_DATA=$AMIRA_DATA sh scripts/sh/setup_render_env_cluster.sh

# --- Step 2 --- training
AMIRA_DATASETS=$AMIRA_DATA \
AMIRA_DATA_GFX=$AMIRA_DATA/amira_data_gfx \
    abrgen --config path/to/config 

# --- Step 3 --- copy results to user directory
cd $HDD && tar -cf /data/Employees/$USER/slurm_results/RenderResult-$SLURM_JOB_ID.tar ./PhIRM

# --- Step 4 --- finalize
set +e
