FROM ubuntu:20.04

# document usage
LABEL description="This image builds an Ubuntu20.04 image with Blender installed."
LABEL maintainer="Marco.Todescato@de.bosch.com"
LABEL version.base="1.0"

# set docker env since COPY does not expand system env variables
ENV HOME=/root
ENV ABR=/root/amira_blender_rendering

# additional install requirements for AMIRA Blender Rendering:
#  * nano: for debugging (remove when stable)
#  * curl: download blender
#  * xz-utils: uncompress blender tarball
#  * lib*: blender dependencies
RUN apt update \
 && apt install --no-install-recommends -y \
        nano \
        curl \
        xz-utils \
        libx11-6 \
        libxi6 \
        libxxf86vm1 \
        libxfixes-dev \
        libxrender-dev \
        libgl-dev \
        libglu-dev \
        libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Setup .bin folder
RUN mkdir -p $HOME/.bin \
 && echo "# added by Dockerfile" >> $HOME/.bashrc \
 && echo "export PATH=\${PATH}:$HOME/.bin" >> $HOME/.bashrc

# Download blender installation
COPY blender.tar.xz $HOME/.bin/blender.tar.xz

# Setup Blender exe and (sym) links
RUN cd $HOME/.bin \
 && tar xf blender.tar.xz \
 && mv blender-2.91.2-linux64 blender.d \
 && cd blender.d/2.91 \
 && tar cf original_python.tar python \
 # sym links (in $HOME/.bin)
 && ln -s $HOME/.bin/blender.d/blender $HOME/.bin/blender \
 && ln -s $HOME/.bin/blender.d/2.91/python/bin/python3.7m $HOME/.bin/python \
 && ln -s $HOME/.bin/python $HOME/.bin/python3 \
 # sym links (in /usr/bin)
 && ln -s $HOME/.bin/blender /usr/bin/blender \
 && ln -s $HOME/.bin/python /usr/bin/python \
 && ln -s $HOME/.bin/python3 /usr/bin/python3

# Setup blender_pip for package management
RUN export BLENDER_PYTHON_DIR=$HOME/.bin/blender.d/2.91/python/bin \
 && export BLENDER_PYTHON_PATH=$BLENDER_PYTHON_DIR/python3.7m \
 && ${BLENDER_PYTHON_PATH} -m ensurepip \
 && ${BLENDER_PYTHON_PATH} -m pip install -U pip \
 && echo "alias pip-blender='${BLENDER_PYTHON_PATH} -m pip'" >> $HOME/.bashrc \
 && echo "export PATH=\${PATH}:$BLENDER_PYTHON_DIR" >> $HOME/.bashrc \
 && /bin/bash -c "source $HOME/.bashrc"

WORKDIR $HOME
CMD ["bash"]
