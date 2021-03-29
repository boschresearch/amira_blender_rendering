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
    theta = np.cos(x) * np.cos(y)
    phi = np.sin(x) * np.cos(y)
    r = np.sin(y)
    return np.array([theta, phi, r])


def generate_points_on_sphere(n):
    """
    creates a list of points approximately evenly spaced around a unit sphere

    Args:
        n: number of points you want to evenly spread on a sphere
    Returns:
        array of points (x,y,z) on a sphere
    """
    x = 0.1 + 1.2 * n
    s0 = (-1 + 1 / (n - 1))
    ds = (2 - 2 / (n - 1)) / (n - 1)
    list_of_points = [
        spherical_coordinate(
            (s0 + i * ds) * x,
            np.pi / 2. * np.copysign(1, (s0 + i * ds)) * (1. - np.sqrt(1. - abs((s0 + i * ds))))
        ) for i in range(n)]
    return np.array(list_of_points)


def points_on_viewsphere(num_points=30, scale=1, bias=(0, 0, 1.5)):
    """
    Creates a list of XYZ locations in half a sphere around and over (0, 0, 0)

    Args:
        num_locations: number of required locations on the unit half sphere around (0, 0, 0)
        scale, bias: scale and bias relative to unit sphere

    Returns:
        half_sphere_locations (np.ndarray): an array of locations
    """
    sphere_locations = generate_points_on_sphere(2 * num_points)

    if isinstance(scale, (int, float)):
        scale = [scale] * 3

    if isinstance(scale, (int, float)):
        bias = [bias] * 3

    half_sphere_locations = []
    for loc in sphere_locations:
        if loc[-1] >= 0:
            loc = [scale[i] * x + bias[i] for i, x in enumerate(loc)]
            half_sphere_locations.append(tuple(loc))

    # corner case with 2 points --> locations are coincident
    if num_points == 1:
        half_sphere_locations.pop(-1)
    assert (len(half_sphere_locations) == num_points)

    return np.array(half_sphere_locations)


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
        start(float): start of curve length [0, 1]. Default: 0
        end(float): end of curve length [0, 1]. Default: 1

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
    points = center + radius * np.vstack([np.cos(T), np.sin(T), np.zeros(T.size)]).transpose()
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
    circle = points_on_circle(num_points, radius, center)
    z_wave = np.vstack([np.zeros(T.size), np.zeros(T.size), amplitude * (np.cos(frequency * T) - 1)]).transpose()
    points = circle + z_wave
    return points


def points_on_piecewise_line(num_points: int, control_points: dict):
    """Generate num_points on a piecewise line defined by a sequence of
    control points [p0, p1, p2, ...]

    Args:
        num_points(int): number of points to create
        cntrl_points(dict): dictionary of control points for the piecwise line
    
    Returns:
        array of points
    """
    # directions and norms
    directions = np.diff(np.asarray(control_points), axis=0)
    norms = np.linalg.norm(directions, axis=1)
    length = np.sum(norms)
    cum_length = np.cumsum(norms)
    T = np.linspace(0, length, num_points, endpoint=True)
    points = np.empty((num_points, control_points[0].size))

    j = 0
    current_length = 0
    for i, t in enumerate(T):
        if t >= cum_length[j]:
            current_length = cum_length[j]
            j += 1
        points[i, :] = control_points[j]
        if j < len(directions):
            points[i, :] += (t - current_length) * directions[j]
    return points


def random_points(num_points, base_location, scale):
    points = base_location + scale * np.random.randn(num_points, base_location.size)
    return points


def plot_transforms(transforms, plot_axis: bool = False, scatter: bool = False):
    """
    Plot list of given transforms.
    Depending on given arguments, the method plots:
        - only the 3d location of the transform
        - a coordinate system representing the entire transform (rot+loc)

    Args:
        transforms(list(array)): list containing 3d transform (4-dim Matrix)
        plot_axis(bool): if true, plot coordinate system representing complete transform
        scatter(bool): if true, generate only a scatter plot of points. Defatul: False

    NOTE: this function will not show if using blender python distro since matplotlib is installed
    in headless mode.
    For debugging purposes and making this function work, it is necessary to setup ABR using a
    dedicated virtualenvironemnt.
    """
    import matplotlib.pyplot as plt
    # This is not directly called but needed for the 3d plot
    from mpl_toolkits.mplot3d import Axes3D  # noqa

    # collect tranforms
    rotations = []
    translations = []
    for transform in transforms:
        # extract transform
        R = np.asarray(transform.to_3x3().normalized())
        t = np.asarray(transform.to_translation())
        rotations.append(R)
        translations.append(t)

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    if plot_axis:
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
    
    else:
        points = np.asarray(translations)
        if scatter:
            ax.scatter(points[:, 0], points[:, 1], points[:, 2])
        else:
            ax.plot(points[:, 0], points[:, 1], points[:, 2])

    plt.show()
