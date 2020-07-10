#!/bin/bash

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

# This script is intended to be used after rendering on the GPU cluster or,
# in general, after having deployed multiple rendering jobs in order to
# compact all the "compatible" rendered datasets into one single directory.

# required positional argument to select desired datasets basename
BASENAME=${1?Error: no given BASENAME for datasets to housekeep}

# optional data storage directory path
AMIRA_DATA_STORAGE=${2:-/data/Employee/$USER/slurm_results}

# decide for simple upacking or more sofisticated behavior with renaming
# of subdirectories
SIMPLE=${3:-True}

# optional name dataset are unpack to
FROMNAME=${4:-PhIRM}
# optional final directory name to store entire dataset to
OUTNAME=${5:-PhIRM}


if [[ $SIMPLE == True ]]; then

    echo ""
    echo "Running (simple) unpacking with following configuration:"
    echo "BASENAME for .tar to unpack                : $BASENAME"
    echo "Storage directory for .tar balls           : $AMIRA_DATA_STORAGE"
    echo ""
    echo -n "Continue? [Y/N]: "
    read OK
    echo ""
    if [[ $OK == "Y" ]]; then

        cd $AMIRA_DATA_STORAGE

        for f in `ls ./$BASENAME*.tar`; do
            #unpacking
            echo "Unpacking $f"
            tar xf $f
        done
    else
        echo "Aborting..."
        exit 0
    fi

else
    echo ""
    echo "Running (sofisticated) housekeeping with following configuration:"
    echo "BASENAME for .tar to unpack                : $BASENAME"
    echo "Storage directory for .tar balls           : $AMIRA_DATA_STORAGE"
    echo "Original (shared) name of partial datasets : $FROMNAME"
    echo "Final dataset directory name               : $OUTNAME"
    echo ""
    echo -n "Continue? [Y/N]: "
    read OK
    echo ""
    if [[ $OK == "Y" ]]; then

        cd $AMIRA_DATA_STORAGE

        for f in `ls ./$BASENAME*.tar`; do
            # extract substring from tarball name
            TONAME=${f:0:-11}.d
            #unpacking
            echo "Unpacking $f"
            tar xf $f
            # rename
            echo "Renaming current $FROMNAME into $TONAME"
            mv ./$FROMNAME ./$TONAME
        done

        # create final directory.
        # This is done here since fromname and outname can be the same.
        # They might clash in this case.
        mkdir $OUTNAME

        # moving to final directory and pack
        echo "Moving to final $OUTNAME directory and packing..."
        mv $BASENAME*.d $OUTNAME
        tar cf $OUTNAME.tar $OUTNAME

        cd -

    else
        echo "Aborting..."
        exit 0
    fi
fi
