#!/bin/sh


# check env variables
if [ -z "$AMIRA_DATASETS" ];
then
    echo "ERROR: Environment variable AMIRA_DATASETS is not set."
    exit 1
fi

if [ -z "$AMIRA_DATA_GFX" ];
then
    echo "ERROR: Environment variable AMIRA_DATA_GFX is not set."
    exit 1
fi

##
## The Real Deal ™
##
echo "Setting up rendering environment. This might take some time..."

# necessary env variables
AMIRA_DATA_STORAGE=/data/Students/AMIRA/datasets

# first go to target directory
# TODO: maybe go to SSD?
cd $HDD

# create directory structure
mkdir -p data/AMIRA-Datasets/

# copy/extract datasets
tar -C $AMIRA_DATASETS -xf $AMIRA_DATA_STORAGE/OpenImagesV4.tar
# fix wrong directory name
mv $AMIRA_DATASETS/OpenImageV4 $AMIRA_DATASETS/OpenImagesV4


echo "Ready to start rendering"

