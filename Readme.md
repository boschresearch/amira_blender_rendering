# Project Name

* [About](#about)
* [Maintainers](#maintainers)
* [Contributors](#contributors)
* [License](#license)
* [How to use it](#use)
* [How to build and test it](#build)
* [Headless Rendering on the GPU Cluster](#clusterrendering)
* [Used 3rd party Licenses](#licenses)

## About<a name="about"></a>

Tools for photorealistic rendering with Blender, for perception pipeline.

## Maintainers<a name="maintainers"></a>

* [Yoel Shapiro](mailto:Yoel.Shapiro@il.bosch.com)
* [Nicolai Waniek](mailto:Nicolai.Waniek@de.bosch.com)

## Contributors<a name="contributors"></a>

* [Yoel Shapiro](mailto:Yoel.Shapiro@il.bosch.com)
* [Nicolai Waniek](mailto:Nicolai.Waniek@de.bosch.com)

## License<a name="license"></a>

TODO
Especially for external mirrored repos it has to be clear under which license
the software was shipped.

## How to use it<a name="use"></a>

0. Setup the global variable $AMIRA_BLENDER_RENDERING_ASSETS to point to the
   rendering directory. For instance, add the following line to your .bashrc or
   .zshrc:

    export AMIRA_BLENDER_RENDERING_ASSETS="~/path/to/assets/directory"

1. Via GUI - install Blender, open a python window, set system.path to include the module and asset directories and launch the desired commands.
2. As a python package - not supported yet, TBD


## How to build and test it<a name="build"></a>

The test folder uses unittest, you can run it according to deployment method (GUI\package)



## Headless Rendering on the GPU Cluster<a name="clusterrendering"></a>

To render on the GPU cluster using blender 2.80, use the scripts within the
folder `scripts/gpu_cluster`.

First, however, you need to install blender 2.80 locally in your home folder,
because there is no Ubuntu package for it available yet. Note that blender 2.x
is cleared Bosch wide ('accepted') and hence no further clearance is required.


### Installing blender

Download the 64bit linux version of blender from blender.org to your local
computer. Then, copy the downloaded .tar.bz2 file to the cluster (for
instance with scp), unpack it, and ideally set up a useful symlink.

The following assumes that you have the following layout of files in your home
folder:

    $ ~/bin                     # folder with executables, scripts, etc.
    $ ~/bin/blender-2.80.d      # un-packed blender download
    $ ~/bin/blender             # symlink to ~/bin/blender-2.80.d/blender

Now, make sure that ~/bin is on your path. For this, open the file ~/.bashrc on
the GPU cluster and add the line

    export PATH="~/bin:$PATH"

at the end of the file (or add ~/bin to the beginning of an already existing
PATH export).


### Using blender and pip to install python packages in a virtualenv

Blender, when installed as above, ships its own python binary. This leads to
issues when trying to install third party libraries due to numpy version
mismatches. The following replaces the shipped python version with the python of
a virtualenv. It is assumed that blender was installed as above to
~/bin/blender.

    $ mkvirtualenv blender-venv                  # This creates a new virtual environment.
                                                 # The path to the venv depends on your system
                                                 # setup. By default, it should end up in
                                                 # ~/.venvs or something similar. In the
                                                 # example here, we assume that virtualenvs
                                                 # are created in ~/venvs
                                                 # Note that this also activtes the venv,
                                                 # which should be indicated by
                                                 # `(blender-env)` in front of PS1 (the dollar
                                                 # sign that indictes your shell $).
    (blender-venv) $ cd bin/blender.d/2.80
    (blender-venv) $ mv python original.python   # make back up of shipped python
    (blender-venv) $ ln -s ~/venvs/blender-venv python
    (blender-venv) $ cd ..
    (blender-venv) $ ./blender -b --python-console

You can exit the shell with Ctrl-D.

If the last step (runnign blender with an interactive python shell) fails,
something went wrong. Quite curiously, blender will report that it found a
bundled python at /home/username/bin/blender.d/2.80/python and reports the
python version that it found as 3.7.0.

Now you can install python packages with pip, which are then also available from
within blender. For instance, to install numpy, imageio, and torch, simply run
the following

    (blender-venv) $ pip install numpy imageio torch

Running blender with an interactive shell, you should now be able to import
numpy, torch, etc.

    (blender-venv) $ blender -b --python-console
    >>> import numpy, torch, imageio

To install packages that are frequently used, go to the `amira_perception`
repository, and consult the requirements.txt file. Or, run the following:

    (blender-venv) $ cd path/to/amira_perception
    (blender-venv) $ pip install -r requirements.txt

Finally, you can test if everything worked by running one of the render scripts.
For instance

    (blender-venv) $ cd path/to/amira_blender_rendering
    (blender-venv) $ blender -b -P scripts/render_dataset_RenderedObjects.py


## Installing the blender-render scripts

Copy the scripts from `scripts/gpu_cluster` to the GPU cluster to ~/bin. Then,
make the script `blender_headless_render` executable

    $ chmod +x ~/bin/blender_headless_render


### Using the GPU cluster for rendering

To render a .blend file on the GPU cluster, simpy use the
`blender_headless_render` script instead of blender. This script will load cuda
modules, pass the .blend file to blender, and also activat all CUDA devices.
Note that additional arguments will be passed to blender

Example (folder gfx contains .blend files):

    $ cd gfx
    $ blender_headless_render materialtest_metal_shaft.blender -o renders/test.png


### Using CUDA rendering in a blender script

To use CUDA rendering on the GPU cluster and automatically select all devices
in another blender script, simply use/copy the function `activate_cuda_devices` from
file `scripts/gpu_cluster/_blender_cuda_render.py`.

The function is also available as`amira_blender_rendering.blender_utils:activate_cuda_devices`.
It is recommended to use this function and not the script provided in
`scripts/gpu_cluster` whenever possible.



## Used 3rd party Licenses<a name="licenses"></a>

This pacakge dependencies include Blender, using the Cycles rendering engine.

Software | License
------------------
[Blender](https://www.blender.org/about/license/) | [GPL](http://www.gnu.org/licenses/gpl-3.0.html)
[Cycles Rendering Engine](https://www.blender.org/about/license/) | [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.txt)



