#!/bin/bash

# go to top level folder
pushd ../..
for f in `ls config/PhIRM-DLR/cfgs/tmp-Detection*.cfg`; do
    echo "Rendering configuration file '$f'"
    abrgen --abr-path ~/amira_blender_rendering/src --config $f
done
popd
