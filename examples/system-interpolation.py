#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

import matplotlib.pyplot as plt

from tathu.geometry.constants import EXAMPLE_GEOMETRY
from tathu.geometry import transform
from tathu.tracking.system import ConvectiveSystem

from datetime import datetime

def plot(geoms, colors=None):
    plt.figure()
    for g in geoms:
        y = []; x = []
        points = g.GetGeometryRef(0).GetPoints()
        for p in points:
            y.append(p[0]); x.append(p[1])
        plt.plot(x, y)

geom = EXAMPLE_GEOMETRY
translated = transform.translate(geom, 5, 5)

# Create start system (08/April/2024 - 12:00)
start_system = ConvectiveSystem(geom)
start_system.timestamp = datetime.strptime('202404081200', '%Y%m%d%H%M')

# Create end system (08/April/2024 - 12:05)
end_system = ConvectiveSystem(translated)
end_system.timestamp = datetime.strptime('202404081205', '%Y%m%d%H%M')

# Interpolate!
systems = transform.interpolate(start_system, end_system, step=1)

# Plot start system and end system
plot([start_system.geom, end_system.geom])

# Plot start system and end system + interpolated geometries
geometries = [start_system.geom, end_system.geom]
for s in systems:
    geometries.append(s.geom)
plot(geometries)

plt.show()
