# Directory and File Format Specification

Every dataset rendered using ABR follows the same folder and annotation structure.
In the following we describe them both.

## Output Folder Structure

Every dataset rendered, e.g., by running

```bash
$ abrgen --config path/to/config.cfg
```

follows the same folder structure. Assuming that 

```python
[dataset]
base_path = RootDir/BaseName

[scene_setup]
cameras = Camera  # only frontal view (mono) camera
```

it consists of the following

> RootDir/  
>   └── BaseName.Camera  
>    ├── Dataset.cfg: summary configuration for rendered dataset  
>    ├── Images/  
>    |  ├── backdrop/  : folder with background drop images (composite mask)  
>    |  ├── range/     : folder with range (.exr) images  
>    |  ├── depth/     : folder with depth (.png) images  
>    |  ├── disparity/ : (if set in the config file) folder with disparity (.png) images  
>    |  ├── masks/     : folder with mask for each segmented object  
>    |  └── rgb/       : folder with RGG images  
>    └── Annotations/  
>       ├── OpenCV/ : [annotations](#annotations) with object poses in OpenCV convention  
>       └── OpenGL/ : [annotations](#annotations) with object poses in OpenGL convention

## Image indexing

All image files (except for masks) are named based on the indexing scheme `sXXX_vYYY`
where XXX and YYY are index determined depeding on the selected number of images and `render-mode`.

For more info about the `render-mode` refer to [render-modes](./using.md#render-modes).

For you to know, in `DEFAULT` render mode XXX wgoes from 0 to N-1 where N is the total number
of images in the dataset while YYY=0. 
In `MULTIVIEW` mode, XXX goes from 0 to S-1 where S is the selected number of scenes, 
while YYY goes from 0 to V-1 where V is the selected number of camera views.
In this case the total number of images is SxV.
Notice that, if necessary, XXX and YYY are zero-padded automatically.

In order to distinguish different instances of objects as well as different object types,
for masks we use the different convention sXXX_vYYY_t_i.png where:

* t : index for the object type
* i : instance number for the same object type


## Annotation File Contents<a name="annotations"></a>

Annotations are stored as .json files following the same naming convention used for images.
That is to image n.png corresponds the annotation n.json, being n the image number.

Each annotation file contains information about all the objects present in the scene in the form
of a list of dictionaries where each dictionary refer to one object instance.

Specifically, for each object we store:

* object_class_name  (str):  label/name for object type
* object_class_id    (int):  object type
* object_name        (str):  instance name
* object_id          (int):  instance number for object of same type
* mask_name          (str):  mask suffix
* visible            (bool): visibility flag
* pose               (dict): dictionary containing:
    - q (list (4,)): object rotation w.r.t. the camera embedded as a quaternion (xyzw)
    - t (list (3,)): object translation vector w.r.t. the camera

* bbox (dict): dictionary containing bounding boxes information:
    - corners2d (list (2,2)): 2d bounding box corners in pixel space
    - corners3d (list (9,2)): 3d bounding box corners in (sub)pixel space 
    - aabb (list (9,3)): axis aligned bounding box corners in 3D space
    - oobb (list (9,3)): object oriented bounding box corners in 3D space

* camera_pose (dict): dictionary containing:
    - q (list (4,)): camera rotation w.r.t. the world frame embedded as a quaternion (xyzw)
    - t (list (3,)): camera translation vector w.r.t. the world frame


## ABR Datasets API (abr_dataset_tools)<a name="ABR-dataset-API></a>

ABR ships also a standalone lean python package to handle datasets rendered using it.

To access ABR's Datasets API, you need to install the abr_dataset_tools package in your working
python environment by running (from the package root directory) (assuming pip3.7)

```bash
(active venv)$ pip install .
```

Then, to have a quick overview of how to use it, run

```bash
(active venv)$ python -m abr_dataset_tools --help
```

The package implements some basic functionalities to load/plot images and print information
about a prescribed dataset.

