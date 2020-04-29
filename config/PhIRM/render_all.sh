#!/bin/bash

# go to top level folder
pushd ../..
for f in `ls config/PhIRM/Workstation-*.cfg`; do
    echo "Rendering configuration file '$f'"
    abrgen --config $f
done
popd
