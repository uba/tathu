#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""
Fit Ellipse
================================

This is a general example demonstrating how use ``fitEllipse`` method for a given geometry object.
"""

import matplotlib.pyplot as plt

from tathu.geometry.constants import EXAMPLE_GEOMETRY
from tathu.geometry.utils import fitEllipse

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
ellipse = fitEllipse(geom)

plot([geom, ellipse])
