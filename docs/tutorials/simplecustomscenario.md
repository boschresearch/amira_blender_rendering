# Set Up a Simple Custom Scenario

ABR allows you to setup and render your own scenario.

For further details and to take inspiration refer to the existing
scenarios located in src/amira_blender_rendering/scenes/

In order to setup your custom scenario few necessary requirements
must be met.

1. [custom classes](#custom-classe)
2. [discove scenes](#discover-scene)

**NOTE** Adding custom scenes requires ABR to be installed as `editable` (see [installation](../installation.md)).


## Create the configuration and scene classes<a name="custom-classes"></a>


Start by creating a new .py file (e.g. `mycoolscenario.py`) in `src/amira_blender_rendering/scenes`.

You could start from a minimal set of imports such as

```python
# necessary imports
import bpy
from amira_blender_rendering.utils import camera as camera_utils
from amira_blender_rendering.utils.io import expandpath
import  amira_blender_rendering.scenes as abr_scenes
import amira_blender_rendering.interfaces as interfaces

# useful imports
import os
import pathlib
from math import ceil, log
import random
import numpy as np
from amira_blender_rendering.utils.logging import get_logger
from amira_blender_rendering.dataset import get_environment_textures, build_directory_info, dump_config
import amira_blender_rendering.utils.blender as blnd
import amira_blender_rendering.nodes as abr_nodes
import amira_blender_rendering.math.geometry as abr_geom
```

As standard in the scenarios already provided, the most natural step is to add
a custom configuration class

```python
# for later convenience, give your scene/scenario a name
_scene_name = 'MyCoolScenario'

# Custom configuration class.
# Inheriting from the BaseConfiguration which defines dataset,
# camera and render -specific configuration parameters.
# abr_scene.register(name=_scene_name, type='config')
class MyCoolScenarioConfiguration(abr_scenes.BaseConfiguration):
    def __init__(self):
        super(MyCoolScenarioConfiguration, self).__init__()

        # Add all the scenario-specific configuration parameters,
        # see the configuration documentation for an overview.
        # This will be accessible in the config file or from the command line.
        self.add_param(...
```

The following and most important thing is to add your custom scenario class

```python
# Custom scenario class.
# Inheriting from ABRScene which defines an interface (in the form of
# an abstract base class) for all ABR scenes.
# This class should be expanded and modified at user wish to implement
# all the functionalities needed to interact with her/his custom scenario.
# E.g., object identification, random pose initialization etc.
@abr_scenes.register(name=_scene_name, type='scene')
class MyCoolScenario(interfaces.ABRScene):
    """
    Example class implementing a custom user-defined scenario
    """
    def __init__(self, **kwargs):
        super(MyCoolScenario, self).__init__()

        # [Optional] some logging capabilities
        self.logger = get_logger()

        # [Recommended] get the configuration, if one was passed in
        self.config = kwargs.get('config', MyCoolScenarioConfiguration())

        # [Mandatory] make use of ABR RenderManager for interaction with Blender
        self.renderman = abr_scenes.RenderManager()

        # [Optional] you might have to post-process the configuration
        self.postprocess_config()

        # [Recommended] set up directories information, e.g., for multiple cameras
        self.setup_dirinfo()

        # [Mandatory] set up anything that we need for the scene before doing anything else.
        # For instance, removing all default objects
        self.setup_scene()

        # [Mandatory] after the scene, let's set up the render manager
        self.renderman.setup_renderer(
            self.config.render_setup.integrator,
            self.config.render_setup.denoising,
            self.config.render_setup.samples,
            self.config.render_setup.motion_blur)

        # [Recommended] setup environment texture information
        # This could be as simple as importing a list of all the available textures.
        # In our case we often use images from OpenImagesV4 as textures for light reflection.
        # In your case this could be a single image or something more sophisticated.
        self.environment_textures = get_environment_textures(self.config.scene_setup.environment_textures)

        # [Mandatory] setup the camera that we wish to use
        self.setup_cameras()

        # [Mandatory] setup render / output settings
        self.setup_render_output()

        # [Mandatory] setup the object that we want to render
        self.setup_objects()

        # [Mandatory] finally, let's setup the compositor
        # by passing it the list of defined objects, see setup_objects.
        self.renderman.setup_compositor(self.objects)


    """
    [Mandatory] You need to implement the abstract methods
    """

    def dump_config(self):
        """
        Dump dataset configuration into corresponding directory for documentation
        """

        # Depending if you are rendering images of a single dataset from a single camera...
        pathlib.Path(self.dirinfo.base_path).mkdir(parents=True, exist_ok=True)
        dump_config(self.config, self.dirinfo.base_path)

        # ...or multiple dataset from multiple cameras
        # See setup_dirinfo()
        for dirinfo in self.dirinfos:
        output_path = dirinfo.base_path
        pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
        dump_config(self.config, output_path)


    def generate_dataset(self):
        """
        Main method used to iterate over and generate the dataset

        The method should implement all the necessary computations to manipulate
        existing objects, call to render and postprocessing

        At generation time, this is called by the main script abrgen,
        which, in turn, calls cli/render_dataset.py
        """

        # Please refer to abr/scenes/simpletoolcap.py or abr/scenes/workspacescenario.py
        # for code-specific implementation.
        # The method could require implementation of additional supporting ones as for instance
        # - visibility tests
        # - object pose randomization
        # - phisics forward simulation
```


Recall, that the above code is only meant to hint your own one. After the constructor,
you are left with implementing the class methods. In the following we provide some examples.


```python
# [Recommended] Set up directories information, e.g., for multiple cameras
def setup_dirinfo(self):

    # This could be a single line of code such as
    self.dirinfo = build_directory_info(self.config.dataset.base_path)

    #.. as well as a list of multiple dictionaries depending if you have
    # one or multiple cameras
    self.dirinfos = list()
    for cam in self.config.scene_setup.cameras:
        camera_base_path = f"{self.config.dataset.base_path}-{cam}"
        dirinfo = build_directory_info(camera_base_path)
        self.dirinfos.append(dirinfo)
```


```python
# [Mandatory] set up anything that we need for the scene before doing anything else.
# For instance, removing all default objects
def setup_scene(self):
    # This highly depends on your scene.

    """[For more complicated scene which use blender modeling]"""
    # You might just want to load the blender file where you previously modeled your scene...
    bpy.ops.wm.open_mainfile(filepath=expandpath(self.config.scene_setup.blend_file))
    # ...plus some additional operation such as
    self.logger.info("Hiding all dropzones from viewport")
    bpy.data.collections['Dropzones'].hide_viewport = True

    """[For simple rendering of objects]"""
    # Conversely, if you do not really have an explicit scene you might
    # first, want to delete everything (just to be sure)...
    blnd.clear_all_objects()
    # ... After you could setup lighting.
    self.lighting = abr_scenes.ThreePointLighting()
```

```python
# [Mandatory] setup the camera that we wish to use
def setup_cameras()
    # This highly depends on your scene and the cameras that are setup in the blender file

    # We recommend to take a look at abr/scenes/simpletoolcap.py or abr/scenes/workstationscenarios.py

    # The general workflow is:
    # - get the intrinsic from the config and convert them into suitable format, e.g., K matrix
    # - select each existing camera and set its intrinsic values
```

```python
# [Mandatory] setup render / output settings
def setup_render_output()
    # This mainly serves to set up the render dimension

    if (self.config.camera_info.width > 0) and (self.config.camera_info.height > 0):
        bpy.context.scene.render.resolution_x = self.config.camera_info.width
        bpy.context.scene.render.resolution_y = self.config.camera_info.height

    # In addition you might want to include additional custom operations...
```

```python
# [Mandatory] setup the object that we want to render
self.setup_objects()
"""
Setup all objects of interest to control in the scene.
The main purpose is to create a list of objects (dict) such as
each object is a dictionary with the following structure

obj = {
    'id_mask'    (str)      : '',
    'model_name' (str)      : obj_type,
    'model_id'   (int)      : model_id,
    'object_id'  (int)      : j,
    'bpy'        (bpy.obj)  : bpy (blender) obj
})

"""

# For code-specific implementation please refer to
# abr/scenes/simpletoolcap.py and/or abr/scenes/workspacescenarios.py
```



## Make the custom scene `discoverable`<a name="discover-scene"></a>

As you might have noticed, right before the class definition for your custom scene and 
its corresponding configurations, we used the following syntax

```python
_scene_name = 'MyCoolScenario'

@abr_scene.register(name=_scene_name, type='config')
class MyCoolScenarioConfiguration(abr_scenes.BaseConfiguration):
    def __init__(self):
        # additional code


@abr_scenes.register(name=_scene_name, type='scene')
class MyCoolScenario(interfaces.ABRScene):
    def __init__(self, **kwargs):
        # additional code
```


In particular, the line `@abr_scene.register(name=, type=)` might appear a bit  obscure 
if you are not familiar with python.
In any case, it is important to add this line to  your custom code. 
Internally, it is used to *automatically* register your scene (and its configuration), 
expose and make it available to ABR.
If you do not add those lines and you try to run `abrgen` with your brand new scene you most 
likely are going to encounter a 

```bash
RuntimeError: Invalid configuration: Unknown scene_type MyCoolSceneario
```

**NOTE** In the config file used at rendering time, you need to use the value set in 
`_scene_name` to correctly select your custom scenario.
