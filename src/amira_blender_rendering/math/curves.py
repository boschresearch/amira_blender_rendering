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

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def points_on_bezier(num_points: int, p0: np.array, p1: np.array, p2: np.array, start: float = 0, stop: float = 1):
    """Generate desired number of points on a 3rd order Bezier curve
    with given control points.
    The curve starts at p0, passes next to p0 and p1 (used to control shape) and ends close to p0

    Args:
        num_points(int): number of points on the curve
        p0(2d/3d array): 2d/3d start point of curve
        p1(2d/3d array): 2d/3d first control point of curve
        p2(2d/3d array): 2d/3d second control point of curve

    Optional Args:
        start(float): start of curve lenght [0, 1]. Default: 0
        end(float): end of curve lenght [0, 1]. Default: 1

    Returns:
        list of points
    """
    points = []
    for t in np.linspace(start, stop, num_points, endpoint=False):
        p = (1 - t)**3 * p0 + 3 * (1 - t)**2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p0
        points.append(p)
    return points


def points_on_circle(num_points: int, radius: float = 1, center: np.array = np.array([0, 0, 0])):
    """Generate points on a 3d circle (of given radius) embedded in
    an x,y-plane centered at the given center

    Args:
        num_points(int)

    Optional Args:
        radius(float)
        center(np.array)
        
    Returns:
        list of points
    """
    points = []
    for t in np.linspace(0, 2 * np.pi, num_points, endpoint=False):
        p = center + np.array([radius * np.cos(t), radius * np.sin(t), 0])
        points.append(p)
    return points


def points_on_wave(num_points, radius: float = 1, center: np.array = np.array([0, 0, 0]),
                   frequency: float = 1, amplitude: float = 1):
    """Generate points on a circular-sinusoidal shaped curve.
    That is a 3d circle of radius `radius` centered at `center` embedded in an x,y-plane
    with superposed a coosinusoidal curve with amplitude `amplitude` and frequency `frequency`
    embedded along the negatve z-axis

    Args:
        num_points(int)
    
    Optional Args:
        radius(float): radius of circle
        center(np.array): center of circle
        frequency(float): cosine wave frequency
        amplitude(float): cosine wave amplitude

    Returns:
        list of points
    """
    points = []
    for t in np.linspace(0, 2 * np.pi, num_points, endpoint=False):
        # point on circle
        p_c = center + np.array([radius * np.cos(t), radius * np.sin(t), 0])
        # point on sin wave
        p_w = np.array([0, 0, amplitude * (np.cos(frequency * t) - 1)])
        # overall point
        points.append(p_c + p_w)

    return points


def plot_points(points):
    """
    3D plot of generated points
    """
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot(points[:, 0], points[:, 1], points[:, 2])
    plt.show()
