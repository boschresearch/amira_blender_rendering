#!/bin/bash

# go to top level folder
pushd ../..
for f in `ls config/PhIRM/Workstation-*.cfg`; do
    echo "Rendering configuration file '$f'"
    blender -b -P scripts/render_dataset.py -- --abr-path "`pwd`/src" --config $f
done
popd
