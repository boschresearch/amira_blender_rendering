# amira_blender_rendering

* [About](#about)
* [Maintainers](#maintainers)
* [Contributors](#contributors)
* [License](#license)
* [How it works and how to use it](#use)
* [How to extend with your own scene](#extending)
* [How to build and test it](#build)
* [Documentation](#docs)
* [Installation](#install)
* [Blender installation and modification of default python](#blenderinstall)
* [Headless Rendering on the GPU Cluster](#clusterrendering)
* [Used 3rd party Licenses](#licenses)

**TODOs**: remove unnecessary links after related content has been moved


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
point [render_dataset.py](src/amira_blender_rendering/cli/render_dataset.py) 
which can be called from the command line 
using `blender -b -P src/amira_blender_rendering/cli/render_dataset.py -- additional-parameters`.
Note that this script has some standard parameters that you can query via
``-h``, passed as the additional parameters above. Also, each scene might
provide configurable options.

For the user's convenience, we also provide [abrgen](scripts/abrgen) a wrapper 
function that simplifies calls to render_dataset.py. Using abrgen, rendering is
commenced from the command line using `scripts/abrgen additional-paramaters`.

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
varianles. Here's a list of the variables that we usually use (Name | Description):

$AMIRA_DATASETS | Path to datasets, such as the one produced here, or OpenImagesV4
$AMIRA_BLENDER_RENDERING_ASSETS | Path to additional assets, such as textures
$AMIRA_DATA_GFX | Path to graphics data


## How to extend with your own scene or parts<a name="extending"></a>

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


## Documentation<a name="docs"></a>

From within amira_blender_rendering/docs/ folder run

```bash
make html
```

**Notes**: according to requirements.txt, compiling the documentation requires
sphinx-rtd-theme to be installed in your current python3 environment


## Installation<a name="install"></a>

Please refer to the [documentation](#docs)

**TODOs**:
* make (some) tutorial(s)?


## Troubleshooting<a name="troubleshooting"></a>

Please refer to the [documentation](#docs)

## Used 3rd party Licenses<a name="licenses"></a>

The package dependencies include Blender, using the Cycles rendering engine.

Software | License
------------------
[Blender](https://www.blender.org/about/license/) | [GPL](http://www.gnu.org/licenses/gpl-3.0.html)
[Cycles Rendering Engine](https://www.blender.org/about/license/) | [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0.txt)



