#!/bin/bash

# for more information about the content of this file, see the files
# in the directory $SLURMTEMPLATE on the GPU cluster

# to run this as a batch job, delete the first # in front of the following
# lines. Note that slurm commands are prefixed with #SBATCH (including the #)

# name of this batch job
#SBATCH --job-name=DopeLetterB10k

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
#SBATCH --mail-user=nicolai.waniek@de.bosch.com
#SBATCH --mail-type=begin,end,fail,time_limit_50,time_limit_80,time_limit_90

# maximum time configuration. format: "DAYS-HH:MM:SS", "DAYS-HH", or "HH:MM:SS"
#SBATCH --time "1-00"

# exit on error
set -e

# --- Step 0 --- prepare the environment, and go to the correct folder
echo "System setup"
module load slurm
module load cudnn/9.2_v7.2
source activate pytorch3.6
cd /home/$USER/dev/vision/amira_perception
[ -d $SSD/tmp ] || mkdir $SSD/tmp


# --- Step 1 --- copy files
AMIRA_DATASETS=$HDD/data/AMIRA-Datasets \
    sh scripts/sh/setup_training_env_cluster.sh


# --- Step 2 --- training
AMIRA_DATASETS=$HDD/data/AMIRA-Datasets \
TMPDIR=$SSD/tmp \
    python train.py \
        --config config/train_dope_letterb.cfg \
        --cluster \
        --logging.tensorboard_enabled False \
        --logging.silent False 


# --- Step 3 --- copy results to user directory
cd $HDD && tar -cf /dlc/Employees/$USER/slurm_results/dope-LetterB-10k-$SLURM_JOB_ID.tar ./weights


# --- Step 4 --- finalize
set +e
