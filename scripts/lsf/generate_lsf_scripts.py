#!/usr/bin/env python3

"""
Similar to generate_slurm_scripts.py but intended to be used
in combination with LSF job scheduler.

Script to create the lsfbatch bash directive scripts.

Use with care!
This script is intended to be run from within your local folder
    'amira_blender_rendering/scripts/lsf'

For more info:
  python generate_lsf_scripts.py --help

General usage foresees that desired cfg files have been already generated.
One option to do this is by running

    python config/PhIRM/generate_config.py

Please have a look at how this works before!
"""

# Example configuration to set up using command-line arguments.
# For more info run with --help flag
#
# CFG_BASE_NAME = 'Workstation'
# CFG_BASE_PATH = 'config/PhIRM'
# PY_ENV_NAME = 'blender-env'
# GPU = 2
# CPU = 4
# RAM = 4
# HH = 0
# MM = 0

import argparse
import os
from pathlib import Path


def parse_args():
    """Parse input command-line arguments"""
    parser = argparse.ArgumentParser(description='Build lsf-batch-job deployment scripts')
    # positional arguments
    parser.add_argument('cfg_base_name', type=str, help='Base name of cfg files to build slurm script for')
    parser.add_argument('cfg_base_path', type=str, help='(Absolute) base path to directory containing desired cfgs')
    parser.add_argument('py_env_name', type=str, default='blender-env',
                        help='Name of python environemt used for rendering')

    # optional arguments
    parser.add_argument('--cudnn', metavar='x.y_vM.N.P', type=str, default='10.1_v7.6',
                        help='Cudnn module version to load (Check avail. with "module avail"). Default: 10.1_v7.6')
    parser.add_argument('--conda', metavar='x.y.z-str', type=str, default='4.4.8-readonly',
                        help='Conda module version to load (Check avail. with "module avail"). Default: 4.4.8-readonly')
    parser.add_argument('--gpu', metavar='N', type=int, default=2,
                        help='Number of required GPUs for batch job. Default: 2')
    parser.add_argument('--gpu-type', metavar='type', type=str, dest='gpu_type', default='rb_regular',
                        help='Type of GPU to load [rb_regular, rb_highend]. Default: rb_regular')
    parser.add_argument('--job-slots', metavar='N', type=int, dest='job_slots', default=1,
                        help='Number of job slots to instantiate. Default: 1')
    parser.add_argument('--cpu', metavar='N', type=int, default=4,
                        help='Number of required CPUs for batch job. Default: 4')
    parser.add_argument('--ram', metavar='N', type=int, default=4,
                        help='RAM to allocate (in GB) per job slots. Default: 4')
    parser.add_argument('--hh', type=int, default=0, help='Number of hours of life for the batch job. Default: 0')
    parser.add_argument('--mm', type=int, default=5, help='Number of mins of life for the batch job. Default: 5')
    parser.add_argument('--amira-storage', metavar='pa/th', type=str, dest='amira_storage',
                        default='/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA',
                        help='Directory where read data are located. \
                              Default: /fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA')
    parser.add_argument('--abr-path', metavar='pa/th', type=str, dest='abr_path',
                        default='$HOME/amira_blender_rendering',
                        help='(Absolute) path to amira_blender_rendering root directory. \
                              Default: $HOME/amira_blender_rendering')
    parser.add_argument('--heavy-duty-dir', metavar='pa/th', type=str, dest='heavy_duty_dir',
                        default='$HOME/lsf_results',
                        help='(Absolute) path to base dir used during heavy duty computations (must exists). \
                              Default: $HOME/lsf_results')
    parser.add_argument('--out-dir', metavar='pa/th', type=str, dest='out_dir',
                        default='/fs/scratch/rng_cr_bcai_dl/$USER/lsf_results',
                        help='(Absolute) path where data are moved to for storage after rendering (must exists). \
                              Default: /fs/scratch/rng_cr_bcai_dl/$USER/lsf_results')

    # parse
    args = parser.parse_args()

    print('\nMake sure you correctly set the desired values for all necessary arguments.\n\
Conversely default values will be used and these might affect the lifespan of the batch job\n')

    return args


# Configuration file parts
def get_scheduler_directives(job_name: str = 'BlenderRender',
                             gpu: int = 2,
                             gpu_type: str = 'rb_regular',
                             job_slots: int = 1,
                             cpu: int = 4,
                             ram: int = 4,
                             hh: int = 0,
                             mm: int = 5):
    """
    Set up slurm directives

    Args:
        job_name(str): job name
        gpu(int): number of required GPUs. Default: 2
        gpu_type(str): type of GPUs, [rb_regular: GeForce, rb_highend: VOLTAS]. Default: rb_regular
        job_slots(int): number of job slots. Default: 1
        cpu(int): number of required CPUs per job slot. Detault: 4
        ram(int): RAM (in GB) to allocate per job slot. Default: 4 GB
        hh(int): hours the job should live. Default: 0
        mm(int): minutes the job should live. Default: 5

    Returns:
        formatted str with directives
    """

    return f"""# name of this batch job
#BSUB -J {job_name}
#
# output configuration
#BSUB -o /home/%u/lsf_out/%x.%j.out
#BSUB -e /home/%u/lsf_out/%x.%j.err
#
# GPU, CPU, MEM configuration
#BSUB -gpu "num={gpu}"
#
# specify type of GPU. rb_regular are GeForce. rb_highend are VOLTAS
#BSUB -q {gpu_type}
#
# number of job slots.
#BSUB -n {job_slots}
#
# number of CPU cores per job slot.
#BSUB -R "affinity[core({cpu})]"
#
# RAM per core in MB
#BUSB --M {ram}000
#
# Mail notifications (begin and end)
#BSUB -B
#BSUB -N
#
# Time configuration "hours:minutes"
#BSUB -W "{hh}:{mm}"
#
# Make sure all jobs slots run on same host
#BSUB -R "span[hosts=1]"
"""


def gen_script(cfgfile: str,
               job_name: str = 'BlenderRender',
               py_env_name: str = 'blender-env',
               cudnn_version: str = '10.1_v7.6',
               conda_version: str = '4.4.8-readonly',
               gpu: int = 2,
               gpu_type: str = 'rb_regular',
               job_slots: int = 1,
               cpu: int = 4,
               ram: int = 4,
               hh: int = 0,
               mm: int = 5,
               amira_storage: str = '/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA',
               abr_path: str = '$HOME/amira_blender_rendering',
               heavy_duty_dir: str = '$HOME/lsf_results',
               out_dir: str = '/fs/scratch/rng_cr_bcai_dl/$USER/lsf_results'):
    """Generate slurm batch script from configs

    Args:
        cfgfile(str): path to cfg file the script is generated for
        job_name(str): job name
        py_env_name(str): name of python environment to use. Default: blender-env
        cudnn_version(str): version of cudnn module to load. Default: 10_v7.3
        conda_version(str): conda module version to load. Default: 4.4.8-readonly
        gpu(int): number of required GPUs. Default: 2
        gpu_type(str): type of GPUs, [rb_regular: GeForce, rb_highend: VOLTAS]. Default: rb_regular
        job_slots(int): number of job slots. Default: 1
        cpu(int): number of required CPUs. Detault: 4
        ram(int): RAM (in GB) to allocate. Default: 4 GB
        hh(int): hours the job should live. Default: 0
        mm(int): minutes the job should live. Default: 5
        amira_storage(str): base path where data are read from. Default: /fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA
        abr_path(str): (absolute) path to amira_blender_rendering root directory. Default: $HOME/amira_blender_rendering
        heavy_duty_dir(str): (absolute) path to base dir used during heavy duty computations (it must exists). Default: $HOME/lsf_results
        out_dir(str): (absolute) path where data are moved to for storage after rendering (it must exists). Default: /fs/scratch/rng_cr_bcai_dl/$USER/lsf_results

    Returns:
        formatted string corresponding to slurm script
    """

    return f"""#!/bin/bash
#
# For more information about the content of this file, see the files
# in the directory $SLURMTEMPLATE on the RNG GPU cluster
#
{get_scheduler_directives(job_name, gpu, gpu_type, job_slots, cpu, ram, hh, mm)}

. /fs/applications/lsf/latest/conf/profile.lsf  # THIS LINE IS MANDATORY
. /fs/applications/modules/current/init/bash    # THIS LINE IS MANDATORY

# exit on error
set -e

# --- Step 0 --- prepare the environment
module purge
module load cudnn/{cudnn_version}
module load conda/{conda_version}
source activate {py_env_name}

# move into amira_blender_rendering root directory
cd {abr_path}

# setup env variables
AMIRA_STORAGE={amira_storage}
SSD={heavy_duty_dir}
HDD={out_dir}

# Make sure the directories exists
if [[ ! -d "$SSD" || ! -d "$HDD" ]]; then
    echo "ERROR: Make sure all necessary repositories exists:"
    echo "SSD : $SSD"
    echo "HDD : $HDD"
    exit 1
fi

# --- Step 1 --- setup
SSD_TMP=`mktemp -d -p $SSD`
tar -C $SSD_TMP -xf $AMIRA_STORAGE/OpenImagesV4.tar
# fix wrong directory name
mv $SSD_TMP/OpenImageV4 $AMIRA_DATA/OpenImagesV4
# copying data gfx
cp -r $AMIRA_STORAGE/amira_data_gfx $SSD_TMP

# --- Step 2 --- render
AMIRA_DATASETS=$SSD_TMP AMIRA_DATA_GFX=$SSD_TMP/amira_data_gfx scripts/abrgen --abr-path {os.path.join(abr_path, 'src')} --config {cfgfile}

# --- Step 3 --- copy results to user directory
cd $SSD_TMP && tar -cf $HDD/{job_name}-$LSF_JOBID.tar ./PhIRM

# --- Step 4 --- clean and finalize
cd $HOME && rm -rf $SSD_TMP
set +e
"""


if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    # extract configs from base name/path
    cfg_path = Path(args.cfg_base_path)
    configs = [c for c in cfg_path.iterdir() if c.name.startswith(args.cfg_base_name)]

    # loop over config files
    for cfg in configs:
        print(f"Generating LSF deployment script for configs {cfg}")
        script = gen_script(cfgfile=cfg,
                            job_name=cfg.stem,
                            py_env_name=args.py_env_name,
                            cudnn_version=args.cudnn,
                            conda_version=args.conda,
                            gpu=args.gpu,
                            gpu_type=args.gpu_type,
                            job_slots=args.job_slots,
                            cpu=args.cpu,
                            ram=args.ram,
                            hh=args.hh,
                            mm=args.mm,
                            amira_storage=args.amira_storage,
                            abr_path=args.abr_path,
                            heavy_duty_dir=args.heavy_duty_dir,
                            out_dir=args.out_dir)
        # write out
        fname = f"tmp-lsfbatch-{cfg.stem}.sh"

        with open(fname, 'w') as f:
            f.write(script)
