![](./media/ABR_rgb_mask.gif)

# amira_blender_rendering

* [About](#about)
* [Maintainers](#authors)
* [Contributors and How to Contribute](#contributors)
* [Documentation](#docs)
* [Installation, How to use it and How to test/troubleshoot](#use)
* [License](#license)
* [Used 3rd party Licenses](#licenses)


## About<a name="about"></a>

AMIRA Blender Rendering: a tool for photorealistic rendering with Blender.

The project is intended to provide a lean programmatic framework for
physics-based photorealistic rendering and make it available to both expert
and beginner user.

The project builds upon [Blender](https://www.blender.org) rendering cababilities and its [Python API](https://docs.blender.org/api/current/index.html) (bpy).


## Original Authors<a name="authors"></a>

* [Nicolai Waniek](mailto:Nicolai.Waniek@de.bosch.com)
* [Marco Todescato](mailto:Marco.Todescato@de.bosch.com)


## Contributors and How to Contribute<a name="contributors"></a>

See [NOTICE](./NOTICE) file for an update list of the current holders
and contributors to AMIRA Blender Rendering.

Also, in case you want to get involve and contribute yourself, please
refer to the [CONTRIBUTING.md](./CONTRIBUTING.md) file and to the 
[documentation](#docs) for more a more in depth description of the workflow.

**Note**: We usually develop against the (default) *develop* branch while *master* 
is used for "stable" releases. Hence consider doing the same when opening PRs.


## Documentation<a name="docs"></a>

From within amira_blender_rendering/docs/ folder run

```bash
make html
```

This will build the documentation under `docs/_build` and can be conveniently
browsed by opening `docs/_build/html/index.html` into you preferred browers.

**Notes**: as explained in the documentation, running ABR *might* require to create
and work with a custom python3.7 environemnt. Hence, it is suggested to create 
one before staring. Also, according to requirements.txt, compiling the documentation 
requires sphinx-rtd-theme to be installed in your current python3 environment.
If you don't know how to create an environment, make sure your python3 system 
distro has sphinx-rtd-theme install in order to build the documentation.


## Installation, How to use it and How to test/troubleshoot<a name="use"></a>

Please refer to the [documentation](#docs)


## License<a name="license"></a>

AMIRA Blender Rendering is opened-source under the Apache-2.0 license. 
as per the [LICENSE](./LICENSE) notice


## Used 3rd party Licenses<a name="licenses"></a>
 
The package dependencies include Blender, using the Cycles rendering engine.
See [3rd party licenses](./3rd-party-licenses.md) for a comprehesinve list.
