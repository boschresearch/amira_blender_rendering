# Using ABR

ABR was developed to be used in headless fashion to render datasets from
pre-defined blender files. For this, we provide the single (command line) 
entry point `abrgen`, to which a user has to pass a configuration file (see
[Configuration](./configs/overview.md) and possibly other command line arguments, 
and which will then invoke blender in the correct manner.

## Using ABR with installation

If you followed our [installation](./installation.md) and installed ABR, e.g., via `pip install`
or `pip install -e`, you can use `abrgen` directly from your command line.
For instance, the following will start producing a dataset specified according
to the configuration `my_config.cfg`:

```bash
$ abrgen --config my_config.cfg
```

If you would like to temporarily alter any configuration option without changing
the configuration file, you can simply pass this as a command line argument to
`abrgen`. For example, assume you would like to change the number of images
that are produced, which is usually stored in the configuration file in section
[dataset](./datasets.md) and has the name `image_count` (see
our [base configuration](./configs/baseconfiguration.md) for more generally available options).
To change this number temporarily, you can invoke `abrgen` with

```bash
$ abrgen --config my_config.cfg --dataset.image_count 123
```

In case you want to discover all options that are available for a certain scene
or Configuration file, you can pass `--help` along to `abrgen`:

```bash
$ abrgen --config my_config.cfg --help
```

Note that this requires a configuration file which specifies at least the scene
type, and will list all parameters that you can modify for the
specified scene. More information about specifying scene types can be found in
our [base configuration](./configs/baseconfiguration.md).

Instead, in case you want to discover all available arguments to call `abrgen`
with you can run

```bash
$ abrgen --help
```


## Using ABR without installation

Sometimes you might not want to or cannot install ABR, or you cannot even run
`abrgen` due to permission issues on the target system. As long as you can
invoke `blender`, you can still make use of ABR, though.

In the first case, that is when you can still run `abrgen`, you can tell it
where to find the ABR package using the `--abr-path` command line argument:

```bash
$ abrgen --abr-path /path/to/ABR/src --config my_config.cfg
```

In the second case, or if you would like to circumvent using `abrgen`, you can
also directly invoke blender. For this to work, you need to locate the file
`render_dataset.py` inside the ABR source tree 
(it should be located in `$ABR/src/amira_blender_rendering/cli` where `$ABR` should
contain the path to ABR root directory), and call blender with the following options:

```bash
$ blender -b -P /path/to/render_dataset.py -- --abr-path /path/to/ABR/src --config my_config.cfg
```


## Using ABR for headless rendering on a GPU cluster

ABR was developed with headless rendering on a GPU cluster in mind. Hence, there
is no significant difference between setting up ABR locally on your computer, or
on a remote system. For more details about how to install ABR, please have a
look at [installation](./installation.md), and for more information about how to use it, see
the sections above.

Nevertheless, we here outline the steps that are often required or recommended
to get rendering going on a headless GPU server. The examples below assume that
your GPU server has a working anaconda installation. We also assume that you
follow good practices and isolate your work into separate virtual environments.

1. create a new conda environment for python 3.7

    ```bash
    $ conda create --name py37 python=3.7
    ```

    This creates a new virtual environment with name `py37`. In our case,
    anaconda create this virtual env in `/software/USERNAME/anaconda/envs/py37`.
    Please note the path that conda reported, as it will be relevant later on.

2. If you haven't done so already, fetch blender in a version that is supported
   by ABR, i.e. >=2.80, and copy it to your GPU cluster. Make sure that the
   blender binary is on your PATH.

3. Replace blender's python with the conda environment's python as described
   in [installation](./installation.md), and run blender to test if it works:

    ```bash
    $ blender -b --python-console
    ```

    This should give you an interactive python shell. Note that you can ignore
    any ALSA errors that might get printed, as we don't consider sound in our
    datasets, and GPU clusters often don't ship with sound cards.

4. Activate your new conda environment and install ABR's dependencies via conda or pip. 
   The example below uses pip.

    ```bash
    $ conda activate py37
    (py37) $ cd /path/to/amira_blender_rendering
    (py37) $ pip install -r requirements.txt
    ```

6. If you haven't done so already, or if your GPU cluster does not provide a
   certain location for common datasets, you might wish to copy required
   datasets (e.g. OpenImages) to a folder that you know and which you can
   specify in Configuration files.

    A good and common practice is to use global variables, e.g. `$DATASET_DIR`,
    that you set in your `.bashrc` or `.zshrc` (or whichever shell you use)
    and which point to folders with such data. This way, you can simply copy your
    local Configuration files to your GPU cluster without having to change
    relevant paths.

    Note that you can make use of all global variables in Configuration files,
    e.g. when specifying environment textures, because we expand all such
    variables before trying to access a path.

7. Finally, use amira_blender_rendering to generate your dataset, e.g.

    ```bash
    $ abrgen --config config/my_config.cfg
    ```

Notice that you do not need to have your environment active to do so. This is
because abrgen and, in turn, blender, will already point to it.


## Environment variables

As mentioned in point 6. above, note that some scenes and/or configurations might 
require you to setup global variables. 
Here's a non-exhaustive) list of the variables that we usually use (Name | Description):

- `$AMIRA_DATASETS`: Path to datasets, such as the one produced here, or OpenImagesV4
- `$AMIRA_DATA_GFX`: Path to graphics data
- `$AMIRA_BLENDER_RENDERING_ASSETS`: Path to additional assets, such as textures


## Rendering modes<a name="render-modes"></a>

Currently, for some of the ready available scenes, ABR offers two different
rendering modes `(DEFAULT, MULTIVIEW)` which can be selected at deployment 
time by running `abrgen` with the flag `--render-mode` followed by the 
name of the mode.

`DEFAULT` refers to the default rendering mode. That is, if no flag is explicitly
selected, this mode is automatically called.
In this mode we usually render one camera view (static-camera) per each (random) scene.
Note that the exact behavior of the render mode depends on the so-called *scene backend*.

`MULTIVIEW` usually refers to the case when we render multiple camera views for
the same (random) scene. That is the camera is *moved* around in 3D space and images
are rendered from each of these camera locations.
Note that how camera locations are selected depends on specific configuration values
to be set in the .cfg file abrgen is called with.

For specific behaviors, refer to the [configurations](./configs/overview.md) docs.
