## https://scholar.rose-hulman.edu/cgi/viewcontent.cgi?article=1387&context=rhumj

import math


def spherical_coordinate(x, y):
    theta = math.cos(x) * math.cos(y)
    phi = math.sin(x) * math.cos(y)
    r = math.sin(y)
    return [theta, phi, r]


def NX(n, x):
    pts = []
    start = (-1. + 1. / (n - 1.))
    increment = (2. - 2. / (n - 1.)) / (n - 1.)
    for j in range(n):
        s = start + j * increment
        pts.append(spherical_coordinate(s * x, math.pi / 2. * math.copysign(1, s) * (1. - math.sqrt(1. - abs(s)))))
    return pts


def generate_points(n):
    return NX(n, 0.1 + 1.2 * n)