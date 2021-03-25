

# Welcome to AMIRA Blender Rendering (ABR)'s documentation!

ABR is a pipeline for rendering large photo-realistic datasets, and is built
around blender_. By using blender_ to model scenes, we allow users to address
their specific requirements with respect to scenarios and model properties with
capabilities of a major and free 3D creation suite. Afterwards, ABR can be used
to handle generation of large amounts of photo-realistic data, for intance to
train deep networks for object recognition, segmentation, pose estimation, etc.

Note that, currently, ABR is operated mostly from the command line. The primary
reason for this is that ABR's intended purpose is also to be used on headless
GPU clusters or rendering farms.

## Workflow

The workflow of using ABR is held as simple as possible.

1. First, in blender_, you either develop your own scenario for which you would
   like to generate a dataset or adapt one of the existing scenarios.
2. If you decided on your own scenario, or if you heavily modified an existing
   scneario, you might need to provide what we call a `scenario backend` which
   will take care of setting up the file. For instance, you might wish to
   randomize object locations in every rendered image.
3. Next, you need to specify rendering information such as camera calibration
   data or the number of images you would like to obtain in a 
   [Configuration](./configs/overview.md)).
4. Finally, you commence dataset generation by running the provided `abrgen`
   command.

As outlined above, each scene requires what we call a *backend implementation*. 
This implementation takes care of loading a blender file, setting up everything that 
is required such as camera information, objects, randomization, etc.
It also contains a `main loop` which does the rendering for the number of desired images. 
An exemplary backend implementation can be found in ABR source tree at
`src/amira_blender_rendering/scenes/workstationscenarios.py`.
This backend implementation reads all optional configuration parameters either
from a configuration file that is passed along to the rendering script, or from
the additional parameters passed during execution.

An example for a configuration that contains documentation for all options can
be found in ABR source tree at `config/examples/workstation_scenario01_test.cfg` .
Note that configuration options depend on the specified blender scene and backend
implementation.

Find out more about [how to use ABR](./using.md) and [Configuration](./configs/overview.md).

## Citing ABR

If you use ABR please make sure to cite our work.

```latex
@misc{amira_blender_rendering_2020,
    author={N.Waniek, M.Todescato, M.Spies, M.Buerger},
    title={AMIRA Blender Rendering},
    year={2020},
    url={https://github.com/boschresearch/amira-blender-rendering},
}
```

## Contacts<a name="contacts"></a>

- [Nicolai Waniek](mailto:n@rochus.net)
- [Marco Todescato](mailto:Marco.Todescato@de.bosch.com)
- [Markus Spies](mailto:Markus.Spies2@de.bosch.com)

