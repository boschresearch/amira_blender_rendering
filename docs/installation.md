
# Installation

This page explains how to install ABR. In order for ABR to properly interact
with blender, it might be necessary to replace the python distribution
shipped with Blender as below explained.
We suggest to first try w/o doing so and resort to it if nothing else works.

**Tested requirements**

The following instructions have been tested for a variety of environments:

* OS: Ubuntu 18.04 (Bionic Beaver) and 20.04 (Focal Fossa)
* Blender: >=2.80, <=2.91.2
* python3.7(.x)

Using a more recent version of Blender should be possible but we do not ensure it.


## Installing ABR as a python package

The easiest way to install (and later use) ABR can be done with `pip`.

If you simply want to use ABR without adding your own scenes or without making
modifications, the best way to install it so is to simply call `pip install .`
from the root of ABR's source tree, i.e. the folder in which you can find the
file `setup.py`. We call this the `passive user mode`.

However, we expect users to be `active`. That is, we believe that, at some
point, you might want to add your own scenes, make modifications to existing
scenes, etc. If you are one of those `active users`, then you should rather
install ABR in editable mode via


```bash
   pip install -e .
```

from ABR's root folder. This way, you can still edit all files, add new scenes,
without having to manually re-install ABR afterwards.

There's also the possibility to use ABR without any installation procedure. More
about this can be found in [using](./using.md).

NOTE: both the above installation commands will install ABR in your currently 
referenced Python distribution. To play around with ABR without messing up
your standard/default distribution, we recommed to create and use a dedicated 
environment, e.g., using Conda or virtualenv.


## (Optional) Setting up blender with a custom python installation

Despite our best efforts, ABR depends, or might in the future depend, on
external libraries that go beyond what blender is shipping. However, installing
third party dependencies using `pip` might not directly work, depending on
your blender version. It is, however, possible, to replace blender's python
version with a locally installed variant. Here, we outline the steps that are
required to setup a python that is installed in a local virtual environment and
make it the one that blender will use on a 64bit computer.

These steps might also be required if you intend to render datasets on a GPU
Cluster that has specific needs for python version, dedicated PIP backends, etc.

**NOTE**: Before you start changing blender as outlined below, we urge you to
try ABR without changing blender's python!


### Installing blender

The example below uses blender-2.80. However, this should also work for later
blender versions. Important is that the python version that should replace
blender's shipped version has the same major and minor version numbers. For
instance, you should be able to replace a python 3.7.0 with python 3.7.5. We
were only partially successful in replacing python when the minor version number
is different (i.e. 3.7.0 vs 3.8.0) due to blender's internal bindings, which
require certain variants of the package `encodings`.

Download the 64bit linux version of [blender](https://www.blender.org) to your local
computer and unpack it in some suitable directory. The next few steps assume
that you have the following layout of files in your `home` folder:

```bash
$ ~/bin                     # folder with executables, scripts, etc.
$ ~/bin/blender-2.80.d      # un-packed blender download
$ ~/bin/blender             # symlink to ~/bin/blender-2.80.d/blender
```

To create the symlink run 

```bash
$ ln -s blender-2.80.d/blender blender
```

Make sure that `~/bin` is on your path (you can add it e.g., through your `~/.bashrc`). 
To quickly test if the setup is correct you can try running `blender` from your command line
which should start Blender's 2.80 GUI.

As mentioned above, blender ships its own python binary. This leads to issues
when trying to install third party libraries due to, e.g., numpy version mismatches. 
There are three ways of dealing with this: Replacing blender's python version with your own virtual environment,
configuring the blender python version to be able to use `pip` or using conda. 

### Replacing Blender's python version

The following replaces the shipped python version with the python of a
virtualenv. 

We assume that blender was installed as above to `~/bin/blender`,
and that you have `virtualenv` or `virtualenvwrapper` installed.

```bash
$ mkvirtualenv blender-venv                  # This creates a new virtual environment.
                                                # The path to the venv depends on your system
                                                # setup. By default, it should end up either in
                                                # ~/.venvs, ~/.virtualenvs or something similar. 
                                                # In the example here, we assume that virtualenvs
                                                # are created in ~/.venvs .
                                                # Note that this also activates the venv,
                                                # which should be indicated by
                                                # `(blender-env)` in front of PS1 (the dollar
                                                # sign that indicates your shell $).
(blender-venv) $ cd bin/blender.d/2.80
(blender-venv) $ mv python original.python   # make back up of shipped python
(blender-venv) $ ln -s ~/venvs/blender-venv python
(blender-venv) $ cd ..
```

We can test if this worked by calling blender and dropping into a python console
from the command line:

```bash
(blender-venv) $ ./blender -b --python-console
```

You can exit the shell with Ctrl-D.

If the last step (running blender with an interactive python shell) failed,
something went wrong. Most likely, you will have received an error which
indicates that a certain package (encodings or initfsencoding) is missing our
could not be loaded. Specifically, you might have received the following
messages:

```
Fatal Python error: initfsencoding: Unable to get the locale encoding
ModuleNotFoundError: No module named 'encoding
```

If this is the case, make sure that your virtualenv was created with a python3.7
virtualenv script, and **neither** with a python2 **nor** a python3.8 virtualenv. 
This could happen if you have a virtualenv script locally installed in ~/.local/bin, 
which points to a python2 environment. 
One viable workaround is to create a python3 environment from which you run the above commands, i.e.

1. Create a python3 environment with your virtualenv installation, e.g.
   called 'py3bootstrap'
2. Locally (i.e., inside the python3 environemnt) install `virtualenv` and `virtualenvwrapper`

```bash
$ (py3bootstrap) pip install virtualenv virtualenvwrapper
```

3. Now create your blender virtual environment

```bash
$ (py3bootstrap) mkvirtualenv blender-venv
```

4. Follow the steps above.

If the aforementioned 4 steps do not work, try to create a python environment
using an explicit call to the appropriate virtualenv:

```bash
$ python3.7 .local/lib/python3.7/site-packages/virtualenv.py blender-env
```

If this still does not solve the issue, please get in contact with us, and we
try to help you out.

### Setting up Blender's python to work with pip

Since version 2.80 blender's python distribution ships with `ensurepip`. This allows you to setup pip in blender. The instructions given here are loosely based on [this](https://blender.stackexchange.com/questions/56011/how-to-install-pip-for-blenders-bundled-python/56013#comment254819_56013) StackOverflow post


```bash
$ export BLENDER_PYTHON_DIR=path/to/blender/2.80/python/bin
$ export BLENDER_PYTHON_PATH=$BLENDER_PYTHON_DIR/python3.7m
$ ${BLENDER_PYTHON_PATH} -m ensurepip
$ ${BLENDER_PYTHON_PATH} -m pip install -U pip
$ # This is just convenience for better usability
$ echo "alias pip-blender='${BLENDER_PYTHON_PATH} -m pip'" >> ~/.bashrc
$ echo "export PATH=\${PATH}:$BLENDER_PYTHON_DIR" >> ~/.bashrc
```

You can test this solution by running

```bash
$ source ~/.bashrc && pip-blender --version
$ # Should point to the blender python distribution
```

**Note**

This procedure has the advantage that you do not need to take care of creating a dedicated python environment
and struggle with selecting the correct interpreter version.
On the other hand, it directly modifies the original Blender's python distro. To minimize the risk of potential
issues we suggest to make a copy of the original python distro.


### Testing your python installation


> The following instructions assume, that you did the virtualenv setup. 
> If you have reconfigured blender's python version, you do not need to work in a virtual environment. 
> Instead, replace all `pip` commands with the pip version of blenders' python distribution. 
> If you followed this tutorial, this should be `pip-blender`

If everything worked as it should, you can now install python packages
within the newly created virtual environment with pip, which are then also available 
from within blender. For instance, to install numpy, imageio, and torch, simply run the following

```bash
(blender-venv) $ pip install numpy imageio torch
```

Running blender with an interactive shell, you should now be able to import
numpy, torch, etc.

```bash
(blender-venv) $ blender -b --python-console
>>> import numpy, torch, imageio
```

without getting an ImportError.

If this worked out, you can finally install ABR in your local virtualenv by running
from ABR root dir (where setup.py is located)

```bash
(blender-venv) $ pip install .
```

or, for the `editable` version

```bash
(blender-venv) $ pip install -e .
```

#### Using Conda

Yet another option is to use conda as a virtual environement and package manager for python.

We assume anaconda3 ([here](https://www.anaconda.com/products/individual) or [here](https://repo.anaconda.com/archive)) is [installed](https://phoenixnap.com/kb/how-to-install-anaconda-ubuntu-18-04-or-20-04)
in your `$HOME` and available on you path. Make sure your version of anaconda python is >= 3.6

Create a conda environment by running

```bash
$ conda create --name blender-venv python=3.7.5 imageio numpy
```

Similar to explained when using virtualenv, symlink blender to the environment. That is, 
from within `~/bin/blender-2.80.d/2.80` run

```bash
$ ln -s ~/anaconda3/env/blender-venv python
```

To check whether this was successfull, run

```bash
$ conda activate blender-venv
(blender-venv) $ blender -b --python-console
```

It this went through you should now be able to use ABR.

**Note**

The advantage of using conda rather than virtualenv is that any anaconda3 version allows you
to select, as interpreter for your environemnt, python3.7.x.
