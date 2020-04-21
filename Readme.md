# amira_blender_rendering

* [About](#about)
* [Maintainers](#maintainers)
* [Contributors](#contributors)
* [License](#license)
* [How it works and how to use it](#use)
* [How to extend with your own scene](#extending)
* [How to build and test it](#build)
* [Blender installation and modification of default python](#blenderinstall)
* [Headless Rendering on the GPU Cluster](#clusterrendering)
* [Used 3rd party Licenses](#licenses)

## About<a name="about"></a>

Tools for photorealistic rendering with Blender.

## Maintainers<a name="maintainers"></a>

* [Nicolai Waniek](mailto:Nicolai.Waniek@de.bosch.com)

## Contributors<a name="contributors"></a>

* [Nicolai Waniek](mailto:Nicolai.Waniek@de.bosch.com)
* [Marco Todescato](mailto:Marco.Todescato@de.bosch.com)
* [Markus Spies](mailto:Markus.Spies2@de.bosch.com)
* [Yoel Shapiro](mailto:Yoel.Shapiro@il.bosch.com)

## License<a name="license"></a>

**TODO**: Add proper license

**TODO**: check license of all external / mirrored repositories / software /
parts that ended up in amira_blender_rendering

## How it works and how to use it<a name="use"></a>

amira_blender_rendering is intended to operate in a headless fashion to render
datasets from pre-defined blender files. For this, we provide a single entry
point [render_dataset.py](scripts/render_dataset.py) which can be called from
the command line using `blender -b -P scripts/render_dataset.py -- additional-parameters`.
Note that this script has some standard parameters that you can query via
``-h``, passed as the additional parameters above. Also, each scene might
provide configurable options.

Each scene requires what we call a *backend implementation*. This implementation
takes care of loading a blender file, setting up everything that is required
such as camera information, objects, randomization, etc. It also contains a
*main loop* which does the rendering for the number of desired images. An
exemplary backend implementation can be found in
[workstationscenarios.py](src/amira_blender_rendering/scenes/workstationscenarios.py).
This backend implementation reads all optional configuration parameters either
from a configuration file that is passed along to the rendering script, or from
the additional parameters passed during execution.

An example for a configuration that contains documentation for all options can
be found in [workstation_scenario01_test.cfg](config/workstation_scenario01_test.cfg).
Note that configuration options depend on the specified blender scene and backend
implementation.

Note that some scenes or configurations might require you to setup global
varianles. Here's a list of the variables that we usually use:

Name | Description
---
$AMIRA_DATASETS | Path to datasets, such as the one produced here, or OpenImagesV4
$AMIRA_BLENDER_RENDERING_ASSETS | Path to additional assets, such as textures


## How to extend with your own scene or parts<a name="extending"><a/>

If you wish to extend `amira_blender_rendering` with your own scenes, you might
want to have a look at the workstation scenario file describe in the previous
section. You can also find backend implementations for simpler scenes in the
folder [src/amira_blender_rendering/scenes](src/amira_blender_rendering/scenes)
in those files starting with `simple*`.

### Adding custom parts to existing scenes

If your scene supports loading additional parts from blender files (such as,
for instance, the WorkstationScenarios), you can specify these files and parts
in an appropriate section in the config file. As an example, have a look at the
aforementioned configuration file.

**Important Notes**.

For this to work properly, make sure that your parts have
the correct scale, as well as rigid object properties. In particular, do not
forget to make the object an active rigid object with appropriate weight and
margins for sensitivity.

Also, make sure that the object's center is approximately at its real-world
physical center. Often, PLY models don't have the object center at the physical
or geometric center of the object. To quickly change this in blender, select the
object and, in object mode, go to the toolbar "Object" -> "Set Origin To" and
select an appropriate variant. Afterwards, it is best to move the object to
location 0, 0, 0. Note that for the provided objects we moved the center to the
geometrical center, as this is the most common usage in downward applications
such as neural networks.

We currently use a default weight of **0.01kg** for most (small) objects and a
sensitivity margin of **0.0001m** for numerical stability.


## How to build and test it<a name="build"></a>

The test folder uses unittest, you can run it according to deployment method (GUI\package)


## Blender installation and modification of default python<a name="blenderinstall"></a>

Despite our best efforts, `amira_blender_rendering` might depend on external
libraries that go beyond what blender is shipping. However, installing third
party dependencies using pip might not directly work, depending on your blender
version. It is, however, possible, to replace python version that ships with
blender with a locally installed version. Here, we outline the steps that are
required to setup a python that is installed in a local virtual environment as
the blender version that blender should use.

These steps might also be required if you intend to render datasets on a GPU
Cluster that has specific needs for python version, dedicated PIP backends, etc.

**NOTE**: Before you start changing blender as outlined below, we urge you to
try `amira_blender_rendering` without changing blender's python!


### Installing blender

The example below uses blender-2.80. However, this should also work for later
blender versions. Important is that the python version that should replace
blender's shipped version has the same major and minor version number. For
instance, you should be able to replace a python 3.7.0 with python 3.7.5. We
were only partially successful in replacing version when the minor version
number is different (i.e. 3.7.0 vs 3.8.0) due to blender's internal bindings, which
require certain variants of the package `encodings`.

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
                                                 # sign that indicates your shell $).
    (blender-venv) $ cd bin/blender.d/2.80
    (blender-venv) $ mv python original.python   # make back up of shipped python
    (blender-venv) $ ln -s ~/venvs/blender-venv python
    (blender-venv) $ cd ..
    (blender-venv) $ ./blender -b --python-console

You can exit the shell with Ctrl-D.

If the last step (running blender with an interactive python shell) fails,
something went wrong. Most likely, you will have received an error which
indicates that a certain package (encodings or initfsencoding) is missing our
could not be loaded. Specifically, you might received the following messages:

    Fatal Python error: initfsencoding: Unable to get the locale encoding
    ModuleNotFoundError: No module named 'encoding

If this is the case, make sure that your virtualenv was created with a python3
virtualenv script, and **not** with a python2 virtualenv. This could happen if
you have a virtualenv script locally installed in ~/.local/bin, which points to
a python2 environment. One viable workaround is to create a python3 environment
from which you run the above commands, i.e.

1) Create a python3 environment with your virtualenv installation, e.g.
   called 'py3bootstrap'
2) $ (py3bootstrap) pip install virtualenv virtualenvwrapper
3) $ (py3bootstrap) mkvirtualenv blender-venv
4) Follow the steps above.

If the aforementioned 4 steps do not work, try to create a python environment
using an explicit call to the appropriate virtualenv:

    $ python3.7 .local/lib/python3.7/site-packages/virtualenv.py blender-env

If this still does not solve the issue, please get in contact with us.

If everything worked, you should end in a python console within blender.  Quite
curiously, blender will report that it found a bundled python at
/home/username/bin/blender.d/2.80/python and reports the python version that it
found as 3.7.0.

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

The following items are of interest if you plan to render on BCAI's internal GPU
cluster.

Copy the scripts from `scripts/gpu_cluster` to the GPU cluster to ~/bin. Then,
make the script `blender_headless_render` executable

    $ chmod +x ~/bin/blender_headless_render


## Headless Rendering on the GPU Cluster<a name="clusterrendering"></a>

If you want to render on the Renningen GPU Cluster, follow the steps outlined
below. Also make sure to set the environment variables that were introduced
above, and have required data (such as environment maps) at proper
locations.

To set up rendering on the GPU cluster, follow the next steps:

1. create a new conda environment for python 3.7

    $ conda create --name py37 python=3.7

   This will create a virtual env in /software/USERNAME/anaconda/envs/py37
   Please note this path, as it will be relevant later on.

2. download blender on your computer, copy it to the GPU cluster, e.g. using
   `scp`, and extract it somewhere such that it is on your path, e.g.  put it
   into ~/bin and create a symlink to the binary

3. activate your new conda environment

    $ conda activate py37

4. Replace blender's python with the conda environment's python as described
   above, and run blender to test if it works:

    $ blender -b --python-console

   This should give you an interactive python shell. Note that you can ignore
   any ALSA errors that might get printed (due to missing sound cards)

5. install dependencies for amira_blender_rendering via conda or pip. The
   example below uses pip.

    $ cd /path/to/amira_blender_rendering
    $ pip install -r requirements.txt

6. Copy required datasets (e.g. OpenImages) to `$AMIRA_DATASETS`

7. Use amira_blender_rendering to generate your dataset

    $ blender -b -P scripts/render_dataset.py -- --config config/workstation_scenario01_train.cfg --abr-path ~/amira/amira_blender_rendering/src


## Troubleshooting<a name="troubleshooting"></a>

1. I get a "CUDA out of memory" exception when rendering, what shall I do?

    Check if the models and scenarios you try to render can be rendered on your
    computer and do not exceed your GPU's RAM limit. To test this, open the file in
    blender and try to render it from the GUI. Blender should indicate how much
    memory it requires for rendering. Compare this value with your GPU RAM.

2. I get a "CUDA out of memory" exception, but I have a GPU with gazillion GB of
   RAM!

    There appears to be an issue for certain scenarios and models that have many
    light sources and different procedural textures. In this case, it happens
    every once in a while, that the BVH that is generated by blender does not
    fit into the GPU. It is currently unclear if this is a blender problem, a
    driver issue, or something unrelated.

    If you experience this issue, try to re-run rendering (both within blender,
    or the scripts), as this issue appears to happen only sporadically. If
    rendering starts from the script, it will finish - rendering and moving data
    to the GPU is performed only in the beginning.

    If re-running does not solve this issue, try to reduce the amount of light
    sources and models in your scenario.

3. Why does forward simulating frames require lots of time?

    The reason for this is that, to drop objects physically correctly, we use
    blenders physics engine (in turn, this is bullet physics), and set the shape
    transform in blender to "Mesh". The time the physics simulation takes
    depends crucially on the model you use, an in particular the number of
    vertices your model has. The rule of thumb is: fewer vertices are faster to
    simulate forward.

    Conclusively, either wait until it's done, or use a low-poly model of your
    target object.


## Used 3rd party Licenses<a name="licenses"></a>

The package dependencies include Blender, using the Cycles rendering engine.

Software | License
------------------
[Blender](https://www.blender.org/about/license/) | [GPL](http://www.gnu.org/licenses/gpl-3.0.html)
[Cycles Rendering Engine](https://www.blender.org/about/license/) | [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.txt)



