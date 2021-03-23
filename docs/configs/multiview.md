
# Multiview Configurations

Multiview configurations can be used to select and setup certain *camera motions*
during `multiview` [render mode](../using.md#render-modes).

A prescribed mode and its corresponding configuration can be selected in the config file 
setting `multiview_setup.mode` and `multiview_setup.mode_cfg`, respectively.

**Notes**

* The number of views along the selected *motion* is controlled by `dataset.view_count`
* By default, the camera views are offset around the inital camera location. This can be disabled
  by setting `multiview_setup.offset=False`.
* Multiview configurations control only location of cameras and not their rotation. In the
  available scenes, all cameras are *rigged* so to always look at a certain 3D location.
  If you plan to develop your custom scene from scratch, it might be worth to consider doing
  something similar.

The following example assumes `random` as a mode.

```python
[multiview_setup]
mode = random
mode_cfg =   
```

## Modes

Currently we provide the following modes:

* `random`: select camera locations randomly in 3D space
* `bezier`: select camera locations along a bezier curve
* `circle`: select camera locations along a circluar trajectory embedded in x-y world plane
* `wave`: select camera locations along a sinusoidal in (z) and circular (in x-y) trajectory
* `viewsphere`: select camera locations from an upper viewsphere
* `piecewiselinear`: select camera locations from a piece-wise linear trajectory


## Mode Configurations

Each mode comes with its specific configurations. Here is an overview.

```python
[multiview_setup]
# Points are generated according to a 3D multivariate Gaussian distribution
mode = random
mode_cfg.base_location = # offset value (mean). Default: 0
mode_cfg.scale = # standard deviation. Default: 1
```

```python
[multiview_setup]
mode = bezier
# Three 3D control points to define the bezier curve.
# Rrandomly selected, if none given
mode_cfg.p0 = # Default: 0
mode_cfg.p1 = # Default: random
mode_cfg.p2 = # Defautl: random
# Where to start and end along the curve assuming it of lenght 1.
mode_cfg.start = # Default: 0
mode_cfg.stop = # Default: 1
```

```python
[multiview_setup]
# The trajectory is embedded in x-y world plane
mode = circle
mode_cfg.radius = # self explanatory. Default: 1
mode_cfg.center = # self explanatory. Default: 0
```

```python
[multiview_setup]
# The "wave" mode forsees a trajectory which is circular in an x-y world plane 
# and sinusoidal along z world-axis.
# This defines a trajectory that while circling around moves the camera up and down.
mode = wave
# as for the circle, radius anc center values
mode_cfg.radius = # Default: 1
mode_cfg.center = # Default: 0
# in addition to the circle
mode_cfg.frequency = # frequency of the sinusodial curve. Deafault: 1
mode_cfg.amplitude = # amplitude along -z of the sinusoidal curve. Default: 1
```

```python
[multiview_setup]
mode = viewsphere
mode_cfg.scale = # approx. max radius of the viewsphere. Default 1
mode_cfg.bias = # center of the view sphere. Default: [0, 0, 1.5]
```

```python
[multiview_setup]
mode = piecewiselinear
# List of control points that defines piece-wise linear chunks of the trajectory
mode_cfg.points = # Default [[0, 0, 0], [1, 1, 1]]
```
