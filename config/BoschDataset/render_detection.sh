#!/bin/bash

HOME=/home/tma2rng
DATA_STORAGE=$HOME/HDD/data
OUTDIR=$HOME/HDD/data/AMIRA-Datasets

# go to top level folder
pushd ../..
for f in `ls config/BoschDataset/cfgs/tmp-*-Detection*.cfg`; do
    echo "Rendering configuration file '$f'"
    DATA_STORAGE=$DATA_STORAGE OUTDIR=$OUTDIR ./scripts/abrgen --abr-path ~/amira_blender_rendering/src --config $f --render-mode multiview
done
popd
