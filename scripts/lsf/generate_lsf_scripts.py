#!/usr/bin/env python3

"""
This module is intended to generate sh script to submit batch jobs
on computing clusters managed with LSF scheduler.

NOTE: Use with care! Please have a look at how this works before!

This script is intended to be run from within your local folder
    'amira_blender_rendering/scripts/lsf'

For more info:
  python generate_lsf_scripts.py --help

Using this module assumes that the desired cfg files have been already generated.
"""

import argparse
import os
from pathlib import Path


def parse_args():
    """Parse input command-line arguments"""
    parser = argparse.ArgumentParser(description='Build lsf-batch-job deployment scripts')
    # positional arguments
    parser.add_argument('cfg_base_name', type=str, help='Base name for (list of) cfg files to build LSF script for')
    parser.add_argument('cfg_base_path', type=str, help='(Absolute) base path to directory containing desired cfgs')

    # optional arguments
    parser.add_argument('--py_env_name', '-py', type=str, default='',
                        help='Name of python environment used for rendering. '
                        'This is not necessary if you set up blender to work with pip and installed ABR '
                        'within blender python distro. Default: ""')
    parser.add_argument('--cudnn', metavar='x.y_vM.N.P', type=str, default='10.1_v7.6',
                        help='Cudnn module version to load (Check avail. with "module avail"). Default: 10.1_v7.6')
    parser.add_argument('--conda', metavar='x.y.z-str', type=str, default='4.5.13',
                        help='Conda module version to load (Check avail. with "module avail"). Default: 4.5.13')
    parser.add_argument('--gpu', metavar='N', type=int, default=2,
                        help='Number of required GPUs for batch job. Default: 2')
    parser.add_argument('--gpu-type', metavar='type', type=str, dest='gpu_type', default='rb_basic',
                        help='Type of GPU to load [rb_basic, rb_highend]. Default: rb_basic')
    parser.add_argument('--cpu', metavar='N', type=int, default=4, help='Number of required CPUs. Default: 4')
    parser.add_argument('--ram', metavar='N', type=int, default=8, help='RAM to allocate (in GB) per core. Default: 8')
    parser.add_argument('--hh', type=int, default=12, help='Number of hours of life for the batch job. Default: 12')
    parser.add_argument('--mm', type=int, default=0, help='Number of mins of life for the batch job. Default: 00')
    parser.add_argument('--data-storage', metavar='pa/th', type=str, dest='data_storage',
                        default='/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA',
                        help='Directory where all read data are located. \
                              Default: /fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA')
    parser.add_argument('--out-dir', metavar='pa/th', type=str, dest='out_dir',
                        default='/fs/scratch/rng_cr_bcai_dl/$USER',
                        help='(Absolute) path where data are moved to for storage after rendering (must exists). \
                              Default: /fs/scratch/rng_cr_bcai_dl/$USER')
    parser.add_argument('--abr-path', metavar='pa/th', type=str, dest='abr_path',
                        default='$HOME/amira_blender_rendering',
                        help='(Absolute) path to amira_blender_rendering root directory. \
                              Default: $HOME/amira_blender_rendering')
    parser.add_argument('--render-mode', type=str, dest='render_mode', default='default',
                        help='Define render mode [default, multiview]. Default: default')

    # parse
    args = parser.parse_args()

    print('\nMake sure you correctly set the desired values for all necessary arguments.\n\
Conversely default values will be used and these might affect the lifespan of the batch job\n')

    return args


# Configuration file parts
def get_scheduler_directives(job_name: str = 'AMIRA-Blender-Rendering',
                             gpu: int = 2,
                             gpu_type: str = 'rb_basic',
                             cpu: int = 4,
                             ram: int = 8,
                             hh: int = 12,
                             mm: int = 0):
    """
    Set up slurm directives

    Args:
        job_name(str): job name
        gpu(int): number of required GPUs. Default: 2
        gpu_type(str): type of GPUs, [rb_basic: GeForce, rb_highend: VOLTAS]. Default: rb_basic
        cpu(int): number of required CPUs per job slot. Detault: 4
        ram(int): RAM (in GB) to allocate per job slot per core. Default: 8 GB
        hh(int): hours the job should live. Default: 12
        mm(int): minutes the job should live. Default: 0

    Returns:
        formatted str with directives
    """

    return f"""# name of this batch job
#BSUB -J {job_name}
#
# output configuration
#BSUB -o /home/%u/.lsf_out/%x.%j.out
#BSUB -e /home/%u/.lsf_out/%x.%j.err
#
# CPU, MEM, GPU, GPU type configuration
#BSUB -n {cpu}
#BSUB -M {ram*1024}
#BSUB -gpu "num={gpu}"
#BSUB -q {gpu_type}
#
# Mail notifications (begin and end)
#BSUB -B
#BSUB -N
#
# Time configuration "hours:minutes"
#BSUB -W "{hh:02d}:{mm:02d}"
#
# Make sure all jobs slots run on same host
#BSUB -R "span[hosts=1]"
"""


def gen_script(cfgfile: str,
               job_name: str = 'AMIRA-Blender-Rendering',
               py_env_name: str = '',
               cudnn_version: str = '10.1_v7.6',
               conda_version: str = '4.5.13',
               gpu: int = 2,
               gpu_type: str = 'rb_basic',
               cpu: int = 4,
               ram: int = 8,
               hh: int = 12,
               mm: int = 0,
               data_storage: str = '/fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA',
               abr_path: str = '$HOME/amira_blender_rendering',
               out_dir: str = '/fs/scratch/rng_cr_bcai_dl/$USER',
               render_mode: str = 'default'):
    """Generate LSF batch script from configs

    Args:
        cfgfile(str): path to cfg file the script is generated for
        job_name(str): job name
        py_env_name(str): name of python environment to use. Default: blender-env
        cudnn_version(str): version of cudnn module to load. Default: 10_v7.3
        conda_version(str): conda module version to load. Default: 4.4.8-readonly
        gpu(int): number of required GPUs. Default: 2
        gpu_type(str): type of GPUs, [rb_basic: GeForce, rb_highend: VOLTAS]. Default: rb_basic
        cpu(int): number of required CPUs. Detault: 4
        ram(int): RAM (in GB) to allocate. Default: 8 GB
        hh(int): hours the job should live. Default: 12
        mm(int): minutes the job should live. Default: 0
        data_storage(str): base path where data are read from. Default: /fs/scratch/rng_cr_bcai_dl/BoschData/AMIRA
        abr_path(str): (absolute) path to amira_blender_rendering root directory. Default: $HOME/amira_blender_rendering
        out_dir(str): (absolute) path where data are moved to for storage after rendering (it must exists).
                      Default: /fs/scratch/rng_cr_bcai_dl/$USER
        render_mode(str): define type of rendering mode ['default', 'multiview']

    Returns:
        formatted string corresponding to slurm script
    """

    return f"""#!/bin/bash
#
#
{get_scheduler_directives(job_name, gpu, gpu_type, cpu, ram, hh, mm)}

. /fs/applications/lsf/latest/conf/profile.lsf  # THIS LINE IS MANDATORY
. /fs/applications/modules/current/init/bash    # THIS LINE IS MANDATORY

# exit on error
set -e

# --- Step 0 --- prepare the environment
module purge
module load cudnn/{cudnn_version}
module load conda/{conda_version}
{'conda deactivate' if py_env_name == '' else f'source activate {py_env_name}'}

# move into amira_blender_rendering root directory
cd {abr_path}

# setup env variables
DATA_STORAGE={data_storage}
OUTDIR={out_dir}

# Make sure the directories exists
if [[ ! -d "$DATA_STORAGE" || ! -d "$OUTDIR" ]]; then
    echo "ERROR: Make sure all necessary repositories exists:"
    echo "OUTDIR : $OUTDIR"
    echo "DATA_STORAGE : $DATA_STORAGE"
    exit 1
fi

# --- Step 1 --- setup
TMP_OUTDIR=`mktemp -d -p $OUTDIR`

# --- Step 2 --- render
OUTDIR=$TMP_OUTDIR \\
DATA_STORAGE=$DATA_STORAGE \\
    scripts/abrgen --abr-path {os.path.join(abr_path, 'src')} \\
                   --config {cfgfile} \\
                   --render-mode {render_mode}

# --- Step 3 --- copy results to user directory
cd $TMP_OUTDIR && tar cf $OUTDIR/{job_name}-$LSB_JOBID.tar *

# --- Step 4 --- clean and finalize
cd $HOME && rm -rf $TMP_OUTIDR
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
                            cpu=args.cpu,
                            ram=args.ram,
                            hh=args.hh,
                            mm=args.mm,
                            data_storage=args.data_storage,
                            abr_path=args.abr_path,
                            out_dir=args.out_dir,
                            render_mode=args.render_mode)
        # write out
        fname = f"tmp-lsfbatch-{cfg.stem}.sh"

        with open(fname, 'w') as f:
            f.write(script)
