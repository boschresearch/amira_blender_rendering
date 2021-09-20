# Basic - Render a predefined scene

To get familiar with ABR, let's run and render a predefined scene.

At the end of this tutorial you should expect to be able to successfully render
a small dataset of images of a metal cap on random backgrounds.
It is assumed ABR is already installed and tested, according to our [installation](../installation.md)


If you are eager to see some images simply jump at the [end](#render) to see how to
commence the rendering.
However, if this is your first time using ABR, we suggest you take a look and
follow the entire tutotial step by step.


## Scene

This tutorial is based on a predefined scene located in
`/src/amira_belender_rendering/scenes/simpleobject.py`
We suggest to take a look at it and try to understand it.
The file can be used as prototypical example in order to set up other scenes.
For a more in depth explanation refer to the following tutorial on
[set up a simple custom sceneario](./simplecustomscenario.md)

Assuming you are familiar with python, a few explanations are in order:

* the class `SimpleObjectConfiguration` is used to manage scene specific config values
* the class `SimpleObject` is used to control the logic of the desired scene.

More specifically, at runtime, after setting up a class object, blender calls the 
`generate_dataset` which, in turn, takes care of:

* randomizing the environment (background) textures
* randomizing the pose of the target object (in this case a metal cap)
* adjust the file paths through the *rendermanager*
* calling the rendering
* performing some post processing steps

```python
def generate_dataset(self):
    # filename setup
    image_count = self.config.dataset.image_count
    if image_count <= 0:
        return False
    format_width = int(ceil(log(image_count, 10)))

    i = 0
    while i < self.config.dataset.image_count:
        # generate render filename: adhere to naming convention
        base_filename = f"s{i:0{format_width}}_v0"

        # randomize environment and object transform
        self.randomize_environment_texture()
        self.randomize_object_transforms()

        # setup render managers' path specification
        self.renderman.setup_pathspec(self.dirinfo, base_filename, self.objs)

        # render the image
        self.renderman.render()

        # try to postprocess. This might fail, in which case we should
        # attempt to re-render the scene with different randomization
        try:
            self.renderman.postprocess(
                self.dirinfo,
                base_filename,
                bpy.context.scene.camera,
                self.objs,
                self.config.camera_info.zeroing,
                postprocess_config=self.config.postprocess)
        except ValueError:
            self.logger.warn("ValueError during post-processing, re-generating image index {i}")
        else:
            i = i + 1

    return True
```


## Data<a name="data"></a>

Make sure the files `B.ply` and `tool_cap_x10.ply` are placed in `/data/cad/parts`.
Also, as background textures we use images from *Open Images* a publicly available
large dataset of various images. Make sure to download they images and store them
locally, e.g., in a dedicated folder in `$HOME/data/OpenImagesV4/Images`.

**Note**: In the tutorial we are going to render images of a metal cap with random background
hence, we do not need any other data (such as a dedicated blender scene). 


## Configuration file

Take a look at the configuration file `/config/examples/single_object_toolcap_example.cfg`.
The file is used to specifiy a bunch of configuration values for the dataset we are
going to render such as the number of images to render etc.

As you can see, we exploits some enviroment variables in order to parametrize some 
configuration values and make them agnostic user specific settings. 
In particular, these are:

* `OUTDIR`: path to folder where the rendered dataset will be stored
* `DATA`: path where backgrounds data are stored
* `DATA_GFX`: path where graphics data are stored

In order to successfully render the dataset, you need to explictly set the above three variables.
You can do that e.g., in you `~/.bashrc` or *inline* as shown in the following section.

## Commence the rendering <a name="render"></a>

Now all that is left is to submit the rendering. It is assumed you have `amira_blender_rendering`
repo available in your `$HOME` and that you set up the data as explained [above](#data).
Then, to commence the rendering run

```bash
OUTDIR=~/data \
DATA_GFX=~/amira_blender_rendering/data \
DATA=~/data \
    abrgen --config ~/amira_blender_rendering/config/examples/single_object_toolcap_example.cfg
```

In case you get

```bash
Error: Could not import amira_blender_rendering. Either install it as a package,
or specify a valid path to its location with the --abr-path command line argument.
```

specify the `--abr-path` CLI argument as explained [here](../using.md#using-wo-installation).