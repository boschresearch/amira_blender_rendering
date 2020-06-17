#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

## https://scholar.rose-hulman.edu/cgi/viewcontent.cgi?article=1387&context=rhumj

import math


def spherical_coordinate(x, y):
    """
    Converts a 2D spiral curve to a 3D spiral curve on a unit sphere

    Args:
        x: abscissa axis
        y: ordinate axis
    Returns:
        theta: angle (around Z)
        phi: angle (around X)
        r: radius
    """
    theta = math.cos(x) * math.cos(y)
    phi = math.sin(x) * math.cos(y)
    r = math.sin(y)
    return [theta, phi, r]


def generate_points(n):
    """
    creates a list of points approximately evenly spaced around a unit sphere

    Args:
        n: number of points you want to evenly spread on a sphere
    Returns:
        list of points (x,y,z) on a sphere
    """
    x = 0.1 + 1.2 * n
    s0 = (-1 + 1 / (n - 1))
    ds = (2 - 2 / (n - 1)) / (n - 1)
    list_of_points = [spherical_coordinate((s0 + i * ds) * x, math.pi / 2. * math.copysign(1, (s0 + i * ds)) * (
            1. - math.sqrt(1. - abs((s0 + i * ds))))) for i in range(n)]
    return list_of_points
