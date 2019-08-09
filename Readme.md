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

## License<a name="license"></a>

TODO
Especially for external mirrored repos it has to be clear under which license
the software was shipped.

## How to use it<a name="use"></a>

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

Finally, make sure that ~/bin is on your path. For this, open the file ~/.bashrc
on the GPU cluster and add the line

    export PATH="~/bin:$PATH"

at the end of the file (or add ~/bin to the beginning of an already existing
PATH export).


### Installing the blender-render scripts

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



## Used 3rd party Licenses<a name="licenses"></a>

This pacakge dependencies include Blender, using the Cycles rendering engine.

Software | License
------------------
[Blender](https://www.blender.org/about/license/) | [GPL](http://www.gnu.org/licenses/gpl-3.0.html)
[Cycles Rendering Engine](https://www.blender.org/about/license/) | [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.txt)

