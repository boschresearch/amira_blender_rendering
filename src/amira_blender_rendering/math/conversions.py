#!/usr/bin/env python

"""This file contains helper functions to convert between different units.

The base unit in blender is 'blender units', which most often is taken to
correspond to meters. In the amira_perception project, we usually define
distances in mm. The functions contained in this file simply map from blender to
another unit.

As a general 'solution', we also assume that blender units correspond to m. Make
sure that you define all scenes in this way, or specify the correct conversion
during scene construction.

If you use the basescenemanager, then blender will be set up to represent
everything in the metric system, and to use meters for distances. Although this
is the default in a standard blender installation, you might have changed it by
overwriting the default.blend file. Thus, we'll just set it once.

"""

def bu_to_m(x):
    """Convert blender unit to meters. This is an identity function."""
    return x

def bu_to_cm(x):
    """Convert blender units to cm."""
    return x * 100.0

def bu_to_mm(x):
    """Convert blender units to mm."""
    return x * 1000.0
