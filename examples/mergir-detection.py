#
# This file is part of TATHU - Tracking and Analysis of Thunderstorms.
# Copyright (C) 2022 INPE.
#
# TATHU - Tracking and Analysis of Thunderstorms is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Example for TATHU - Tracking and Analysis of Thunderstorms."""

from tathu.satellite import mergir
from tathu.tracking import detectors
from tathu.tracking.utils import area2degrees
from tathu.visualizer import MapView

# Read data
path = './data/merg_2001010100_4km-pixel.nc4'
grid = mergir.sat2grid(path, fillNoDataValues=False, time=mergir.CompositionTime.ON_THE_HOUR)

# Threshold value
threshold = 220 # Kelvin

# Define minimum area
minarea = 3500 # km^2

# Convert to degrees^2
minarea = area2degrees(minarea)

# Create detector
detector = detectors.LessThan(threshold, minarea)

print('Searching for systems...')
systems = detector.detect(grid)
print('done.')

timestamp = mergir.getTimestamp(path)

# Adjust timestamp
for s in systems:
    s.timestamp = timestamp

# Get data extent
extent = mergir.getExtent(path)

# Show results
m = MapView(extent, timestamp=str(timestamp))
m.plotRaster(grid, cmap='Greys', colorbar=True)
m.plotSystems(systems, facecolor='none', edgecolor='red')
m.show()
