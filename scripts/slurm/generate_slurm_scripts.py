#!/usr/bin/env python3

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

"""
Script to create the slurmbatch bash directive scripts.

Use with care!
This script is intended to be run from within your local folder
    'amira_blender_rendering/scripts/slurm'

For more info:
  python generate_slurm_scripts.py --help

General usage foresees that desired cfg files have been already generated.
One option to do this is by running

    python config/PhIRM/generate_config.py

Please have a look at how this works before!
"""

# Example configuration to set up using command-line arguments.
# For more info run with --help flag
#
# USER = 'marco.todescato'  # user for email
# CFG_BASE_NAME = 'Workstation'
# CFG_BASE_PATH = 'config/PhIRM'
# PY_ENV_NAME = 'blender-env'
# GPU = 4
# CPU = 4
# SSD = 20
# RAM = 32
# DAYS = 1
# HH = 0
# MM = 0

import argparse
import os
from pathlib import Path


def parse_args():
    """Parse input command-line arguments"""
    parser = argparse.ArgumentParser(description='Build slurm-batch-job deployment scripts')
    # positional arguments
    parser.add_argument('user', type=str, help='name.surname of user for receiving emails')
    parser.add_argument('cfg_base_name', type=str, help='Base name of cfg files to build slurm script for')
    parser.add_argument('cfg_base_path', type=str, help='(Absolute) base path to directory containing desired cfgs')
    parser.add_argument('py_env_name', type=str, default='blender-env',
                        help='Name of python environemt used for rendering')

    # optional arguments
    parser.add_argument('--input-flag', type=str, dest='input_flag', default='',
                        help='one additional input flag (without prefix --) for main script')
    parser.add_argument(
        '--cudnn', metavar='x.y_vM.N.P', type=str, default='10.0_v7.3.1',
        help='Cudnn module version to load (Check available running "module avail"). Default: 10.0_v7.3.1')
    parser.add_argument('--gpu', metavar='N', type=int, default=4,
                        help='Number of required GPUs for batch job. Default: 4')
    parser.add_argument('--cpu', metavar='N', type=int, default=4,
                        help='Number of required CPUs for batch job. Default: 4')
    parser.add_argument('--ssd', metavar='N', type=int, default=20,
                        help='Hard drive memory (in GB) to allocate. Default: 20')
    parser.add_argument('--ram', metavar='N', type=int, default=16,
                        help='RAM to allocate (in GB). Default: 16')
    parser.add_argument('--dd', type=int, default=0, help='Number of days of life for the batch job. Default: 0')
    parser.add_argument('--hh', type=int, default=0, help='Number of hours of life for the batch job. Default: 0')
    parser.add_argument('--mm', type=int, default=5, help='Number of mins of life for the batch job. Default: 5')
    parser.add_argument('--amira-data', metavar='pa/th', type=str, dest='amira_data', default='$SSD/data',
                        help='path where data are moved/stored during job execution')
    parser.add_argument(
        '--abr-path', metavar='pa/th', type=str, dest='abr_path', default='$HOME/amira_blender_rendering',
        help='(Absolute) path to amira_blender_rendering root directory. Default: $HOME/amira_blender_rendering')
    parser.add_argument(
        '--out-path', metavar='pa/th', type=str, dest='out_path', default='/data/Employees/$USER/slurm_results/',
        help='(Absolute) path where output data are moved to for storage. Default: /data/Employees/$USER/slurm_results')
    parser.add_argument('--dset-name', metavar='name', type=str, dest='dset_name', default='PhIRM',
                        help='Name of directory with dataset to pack')

    # parse
    args = parser.parse_args()

    print('\nMake sure you correctly set the desired values for all necessary arguments.\n\
Conversely default values will be used and these might affect the lifespan of the batch job\n')

    return args


# Configuration file parts
def get_slurm_directives(user: str,
                         job_name: str = 'BlenderRender',
                         gpu: int = 2,
                         cpu: int = 4,
                         ssd: int = 10,
                         ram: int = 16,
                         days: int = 0,
                         hh: int = 0,
                         mm: int = 5):
    """
    Set up slurm directives

    Args:
        user(str): name.surname of user, to receive email
        job_name(str): job name
        gpu(int): number of required GPUs. Default: 2
        cpu(int): number of required CPUs. Detault: 4
        ssd(int): hard drive (SSD) memory (in GB) to allocate. Default: 10 GB
        ram(int): RAM (in GB) to allocate. Default: 16 GB
        days(int): number of days the job should live. Default: 0
        hh(int): hours the job should live. Default: 0
        mm(int): minutes the job should live. Default: 5

    Returns:
        formatted str with directives
    """

    return f"""# name of this batch job
#SBATCH --job-name={job_name}

# account to which the resources get accounted to
#SBATCH --account=r31

# output configuration
#SBATCH --output=/home/%u/slurm_out/%x.%j.out
#SBATCH --error=/home/%u/slurm_out/%x.%j.err

# GPU, CPU, MEM configuration
#SBATCH --gres=gpu:{gpu},ssd:{ssd}G
#SBATCH --cpus={cpu}
#SBATCH --mem={ram}G

# Mail notifications
#SBATCH --mail-user={user}@de.bosch.com
#SBATCH --mail-type=begin,end,fail,time_limit_50,time_limit_90

# maximum time configuration. format: "DAYS-HH:MM:SS", "DAYS-HH", or "HH:MM:SS"
#SBATCH --time "{days}-{hh}:{mm}:00"
"""


def gen_script(user: str,
               cfgfile: str,
               job_name: str = 'BlenderRender',
               py_env_name: str = 'blender-env',
               input_flag: str = '',
               cudnn_version: str = '10.0_v7.3.1',
               gpu: int = 2,
               cpu: int = 4,
               ssd: int = 10,
               ram: int = 16,
               days: int = 0,
               hh: int = 0,
               mm: int = 5,
               amira_data: str = '$SSD/data',
               abr_path: str = '$HOME/amira_blender_rendering',
               out_path: str = '/data/Employees/$USER/slurm_results',
               dset_name: str = 'PhIRM'):
    """Generate slurm batch script from configs

    Args:
        user(str): name.surname of user, to receive email
        cfgfile(str): path to cfg file the script is generated for
        job_name(str): job name
        py_env_name(str): name of python environment to use. Default: blender-env
        input_flag(str): string with one additional flag for main script. Default ''
        cudnn_version(str): version of cudnn module to load. Default: 10_v7.3
        gpu(int): number of required GPUs. Default: 2
        cpu(int): number of required CPUs. Detault: 4
        ssd(int): hard drive (SSD) memory (in GB) to allocate. Default: 10 GB
        ram(int): RAM (in GB) to allocate. Default: 16 GB
        days(int): number of days the job should live. Default: 0
        hh(int): hours the job should live. Default: 0
        mm(int): minutes the job should live. Default: 5
        amira_data(str): base path where to store data. Default: $HDD/data
        abr_path(str): (absolute) path to amira_blender_rendering root directory. Default: $HOME/amira_blender_rendering
        out_path(str): (absolute) path where data are moved to for storage after rendering.
                        Default: /data/Employees/$USER/slurm_results
        dset_name(str): name of directory with dataset to pack. Default: PhIRM

    Returns:
        formatted string corresponding to slurm script
    """

    return f"""#!/bin/bash

# for more information about the content of this file, see the files
# in the directory $SLURMTEMPLATE on the GPU cluster

# to run this as a batch job, delete the first # in front of the following
# lines. Note that slurm commands are prefixed with #SBATCH (including the #)

{get_slurm_directives(user, job_name, gpu, cpu, ssd, ram, days, hh, mm)}

# exit on error
set -e

# --- Step 0 --- prepare the environment
echo "System setup"
module load slurm
module load cudnn/{cudnn_version}
conda activate {py_env_name}
cd {abr_path}

# setup env variables
AMIRA_DATA={amira_data}

# --- Step 1 --- copy files
AMIRA_DATA=$AMIRA_DATA sh scripts/sh/setup_render_env_cluster.sh

# --- Step 2 --- rendering
AMIRA_DATASETS=$AMIRA_DATA \\
AMIRA_DATA_GFX={os.path.join(amira_data, 'amira_data_gfx')} \\
scripts/abrgen --abr-path {os.path.join(abr_path, 'src')} --config {cfgfile} {'--' + input_flag if input_flag else ''}

# --- Step 3 --- copy results to user directory
cd $AMIRA_DATA && tar -cf {os.path.join(out_path, job_name)}-$SLURM_JOB_ID.tar ./{dset_name}

# --- Step 4 --- finalize
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
        print(f"Generating slurm deployment script for configs {cfg}")
        script = gen_script(user=args.user,
                            cfgfile=cfg,
                            job_name=cfg.stem,
                            py_env_name=args.py_env_name,
                            input_flag=args.input_flag,
                            gpu=args.gpu,
                            cpu=args.cpu,
                            ssd=args.ssd,
                            ram=args.ram,
                            days=args.dd,
                            hh=args.hh,
                            mm=args.mm,
                            amira_data=args.amira_data,
                            out_path=args.out_path,
                            dset_name=args.dset_name)
        # write out
        fname = f"tmp-slurmbatch-{cfg.stem}.sh"

        with open(fname, 'w') as f:
            f.write(script)
