#!/bin/bash

# go to top level folder
pushd ../..
for f in `ls config/PhIRM-DLR/cfgs/tmp-Tracking*.cfg`; do
    echo "Rendering configuration file '$f'"
    abrgen --abr-path ~/amira_blender_rendering/src --config $f --render-mode multiview
done
popd
