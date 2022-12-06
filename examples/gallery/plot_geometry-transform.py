#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""
Geometric Transformation
========================

This is a general example demonstrating geometric transformations (rotate, translate and scale).
"""

import matplotlib.pyplot as plt

from tathu.geometry.constants import EXAMPLE_GEOMETRY
from tathu.geometry import transform

def plot(geoms):
    plt.figure()
    for g in geoms:
        y = []; x = []
        points = g.GetGeometryRef(0).GetPoints()
        for p in points:
            y.append(p[0]); x.append(p[1])
        plt.plot(x, y)
    plt.show()

geom = EXAMPLE_GEOMETRY

rotated = transform.rotate(geom, -45.0)
translated = transform.translate(geom, 5, 5)
scaled = transform.scale(geom, 2.0, 2.0)
translated_rotated = transform.rotate(translated, -90.0)

plot([geom, rotated, translated, scaled, translated_rotated])
