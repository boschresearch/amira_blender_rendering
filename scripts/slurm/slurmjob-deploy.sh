#!/bin/bash

# deploy all desired slurmbatch job

BASENAME=${1?Error: no BASENAME for slurmbatch .sh script to deploy given}

for f in `ls ./$BASENAME*.sh`; do
    echo "Deploying batch job associated to '$f'"
	sbatch  $f
done
