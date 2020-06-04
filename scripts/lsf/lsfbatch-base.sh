#!/bin/bash
# This script describes a typical LSF job script. Comments will explain what the
# specific option does.  All lines starting with # are ignored. LSF commands are
# prefixed by #BSUB and they must start a line. All #BSUB directives after the
# first non-comment line are ignored. To comment out a directive, simply add
# another hash (e.g. ##BSUB)
#
# Give the job a meaningful name.
#BSUB -J BlenderRenderJob
#
# Determine where the output and error will be written. WARNING: if you forget to specify
# this or if the directory does not exist, LSF will not create any output file.
# Make sure the directory already exists.
#BSUB -o /home/%u/lsf_out/%x.%j.out
#BSUB -e /home/%u/lsf_out/%x.%j.err
#
# Specify the number of GPUs to be used per host.
#BSUB -gpu "num=2"
#
# Specify the type of GPU to use. Those are GeForce for rb_regular and Voltas
# for rb_highend.
#BSUB -q rb_regular
# #BSUB -q rb_highend       # use VOLTAS if uncommented
#
# Specify the number of job slots to be used. By default (but not for this
# example), this is also the number of CPUs.
#BSUB -n 1
#
# Specify the number of CPU cores per job slot. A job slot is always guaranteed
# to be on one host. Here, specify 3. The default is 1 CPU per job slot.
#BSUB -R "affinity[core(4)]"
#
# Receive email notifications.  Specify when to receive emails.
#BSUB -B			    # receive email when job starts
#BSUB -N			    # receive email when job ends
#
# Specify RAM PER JOB SLOT in MB that your job will use.
#BSUB -M 5000
#
# Specify the maximum runtime of you job. The format is "hours:minutes".
#BSUB -W 24:00
#
# Make sure that all job slots run on the same host
#BSUB -R "span[hosts=1]"    # run on a single host
#
# Instead of span[hosts=1], you can also specify the number of job slots per
# host the following way (please remember that you specify the number of GPUs
# per host and not per job slot!). Note that only explicitly MPI-enabled jobs
# may run on multiple hosts at the same time. Without MPI, resources not on the
# primary host will simply sit idle.
# #BSUB -R "span[ptile=2]"    # 2 job slots per host

# Please work in /fs/scratch/rng_cr_bcai_dl/$USER or your home directory.  Also
# access your data directly from /fs/scratch/rng_cr_bcai_dl .

. /fs/applications/lsf/latest/conf/profile.lsf  # THIS LINE IS MANDATORY
. /fs/applications/modules/current/init/bash    # THIS LINE IS MANDATORY

# Exit on any error. Do not put this line before the two mandatory ones.
set -e

# --- Step 0 --- prepare environment
# Unload all modules.
module purge
# Load a specific version of CUDA and CUDNN (or any other available version,
# check "module avail" for which ones there are).
module load cudnn/10.1_v7.6
# Make conda available.
module load conda/4.4.8-readonly
source activate blender-env

cd /home/$USER/amira_blender_rendering

# alias for read/write locations
AMIRA_STORAGE=/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA # stored data for reading
SSD=/home/$USER/lsf_results  # heavy duty base directory used for read/write during rendering
HDD=/fs/scratch/rng_cr_bcai_dl/$USER/lsf_results  # out location

# Make sure the directories exists
if [[ ! -d "$SSD" || ! -d "$HDD" ]]; then
    echo "ERROR: Make sure all necessary repositories exists:"
    echo "SSD : $SSD"
    echo "HDD : $HDD"
    exit 1
fi

# --- Step 1 --- setup
# differently from RNG cluster where data are copied into locally created locations
# SI and ABT cluster read/write directly from/to /fs/scratch locations.
# However, because of our use of env variables in config file, we copy some files to
# local user
SSD_TMP=`mktemp -d -p $SSD`
tar -C $SSD_TMP -xf $AMIRA_STORAGE/OpenImagesV4.tar
# fix wrong directory name
mv $SSD_TMP/OpenImageV4 $AMIRA_DATA/OpenImagesV4
# copying data gfx
cp -r $AMIRA_STORAGE/amira_data_gfx $SSD_TMP


# --- Step 2 --- render
AMIRA_DATASETS=$SSD_TMP \
AMIRA_DATA_GFX=$SSD_TMP/amira_data_gfx \
    abrgen --config path/to/config

# --- Step 3 --- copy results to user directory
cd $SSD_TMP && tar -cf $HDD/RenderResult-$LSF_JOBID.tar ./PhIRM

# --- Step 4 --- clean and finalize
cd $HOME && rm -rf $SSD_TMP
set +e
