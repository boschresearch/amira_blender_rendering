#!/bin/sh

# check env variables
if [ -z "$AMIRA_DATA" ];
then
    echo "ERROR: Environment variable AMIRA_DATA is not set."
    exit 1
fi

##
## The Real Deal ™
##
echo "Setting up rendering environment. This might take some time..."

# necessary env variables. used to grab data from
AMIRA_STORAGE=/data/Students/AMIRA/datasets
AMIRA_DATA_GFX_GIT=ssh://git@sourcecode.socialcoding.bosch.com:7999/amira/amira_data_gfx.git

# create directory structure
mkdir -p $AMIRA_DATA

# copy/extract datasets
git clone $AMIRA_DATA_GFX_GIT $AMIRA_DATA/amira_data_gfx
tar -C $AMIRA_DATA -xf $AMIRA_STORAGE/OpenImagesV4.tar
# fix wrong directory name
mv $AMIRA_DATA/OpenImageV4 $AMIRA_DATA/OpenImagesV4

echo "Ready to start rendering"
