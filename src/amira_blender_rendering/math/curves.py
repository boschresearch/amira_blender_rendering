#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np


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
    T = np.linspace(start, stop, num_points, endpoint=False)
    T0 = (1 - T)**3
    T1 = 3 * (1 - T)**2 * T
    T2 = 3 * (1 - T) * T**2
    T3 = T**3
    points = np.outer(T0, p0) + np.outer(T1, p1) + np.outer(T2, p2) + np.outer(T3, p0)
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
        np.ndarray of points
    """
    T = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    points = center + np.vstack([np.cos(T), np.sin(T), np.zeros(T.size)]).transpose()
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
    T = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    points = center + np.vstack([np.cos(T), np.sin(T), amplitude * (np.cos(frequency * T) - 1)]).transpose()
    return points


def plot_points(points, camera=None, plot_axis: bool = False):
    """
    3D plot of generated points
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot(points[:, 0], points[:, 1], points[:, 2])

    # collect tranforms
    if camera is not None and plot_axis:
        import bpy
        rotations = []
        translations = []
        for loc in points:
            # set location
            camera.location = loc
            # update graph
            bpy.context.evaluated_depsgraph_get().update()
            # extract transform
            R = np.asarray(camera.matrix_world.to_3x3().normalized())
            t = np.asarray(camera.matrix_world.to_translation())
            rotations.append(R)
            translations.append(t)

        length = 0.05
        x_axis_0 = np.float32([length, 0, 0])
        y_axis_0 = np.float32([0, length, 0])
        z_axis_0 = np.float32([0, 0, length])

        for R, t in zip(rotations, translations):
            # compute transformed points
            x_axis = R.dot(x_axis_0) + t
            y_axis = R.dot(y_axis_0) + t
            z_axis = R.dot(z_axis_0) + t
            neg_z_axis = R.dot(-30 * z_axis_0) + t
            # plot x
            ax.plot([t[0], x_axis[0]], [t[1], x_axis[1]], [t[2], x_axis[2]], color='r')
            # plot y
            ax.plot([t[0], y_axis[0]], [t[1], y_axis[1]], [t[2], y_axis[2]], color='g')
            # plot z
            ax.plot([t[0], z_axis[0]], [t[1], z_axis[1]], [t[2], z_axis[2]], color='b')
            # virtual neg z
            ax.plot([t[0], neg_z_axis[0]], [t[1], neg_z_axis[1]], [t[2], neg_z_axis[2]], color='b', linestyle='--')   
    plt.show()
